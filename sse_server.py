"""
SSE (Server-Sent Events) Server for Microsoft Copilot Studio
Provides HTTP/SSE transport for MCP protocol
"""

import asyncio
import json
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Import from main server
from server import list_tools, call_tool
from auth import validate_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sse-server")

# Create FastAPI app
app = FastAPI(title="EPIC EHR MCP Server - SSE")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active SSE connections
active_connections = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "EPIC EHR MCP Server",
        "version": "1.0.0",
        "transport": "SSE",
        "endpoints": {
            "sse": "/sse",
            "tools": "/tools",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "transport": "sse"}


@app.get("/tools")
async def get_tools():
    """Get list of available tools (REST endpoint)"""
    try:
        tools = await list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sse")
async def sse_endpoint(request: Request):
    """
    SSE endpoint for MCP protocol
    Copilot Studio connects here to discover and call tools
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        connection_id = id(request)
        logger.info(f"New SSE connection: {connection_id}")
        
        try:
            # Send initial connection message
            yield {
                "event": "connected",
                "data": json.dumps({
                    "type": "connection",
                    "status": "connected",
                    "server": "EPIC EHR MCP Server"
                })
            }
            
            # Send tools list
            tools = await list_tools()
            tools_data = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }
            
            yield {
                "event": "tools",
                "data": json.dumps(tools_data)
            }
            
            logger.info(f"Sent {len(tools)} tools to connection {connection_id}")
            
            # Keep connection alive with heartbeat
            while True:
                await asyncio.sleep(30)
                yield {
                    "event": "ping",
                    "data": json.dumps({"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()})
                }
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@app.post("/call")
async def call_tool_endpoint(request: Request):
    """
    HTTP endpoint to call MCP tools
    Used by Copilot Studio to execute tools
    """
    try:
        data = await request.json()
        
        # Extract parameters
        tool_name = data.get("tool")
        arguments = data.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing 'tool' parameter")
        
        # Validate access token if provided
        access_token = arguments.get("access_token")
        if access_token:
            token_data = validate_token(access_token)
            if not token_data:
                raise HTTPException(status_code=401, detail="Invalid access token")
        
        # Call the tool
        logger.info(f"Calling tool: {tool_name}")
        result = await call_tool(tool_name, arguments)
        
        # Return result
        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [r.model_dump() for r in result]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/authenticate")
async def authenticate_endpoint(request: Request):
    """
    HTTP endpoint for OAuth authentication
    """
    try:
        data = await request.json()
        
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        app_id = data.get("app_id")
        
        if not all([client_id, client_secret, app_id]):
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: client_id, client_secret, app_id"
            )
        
        # Call authenticate tool
        result = await call_tool("authenticate", {
            "client_id": client_id,
            "client_secret": client_secret,
            "app_id": app_id
        })
        
        # Parse result
        result_text = result[0].text
        result_data = json.loads(result_text)
        
        if result_data.get("status") == "success":
            return {
                "access_token": result_data["access_token"],
                "token_type": "Bearer",
                "expires_in": 3600,
                "client_info": result_data["client_info"]
            }
        else:
            raise HTTPException(status_code=401, detail=result_data.get("message", "Authentication failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in authentication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Run SSE server on port 8000
    logger.info("Starting SSE server on http://0.0.0.0:8000")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
