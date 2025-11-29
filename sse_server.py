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


# Middleware to log all requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request
    logger.info(f"=" * 60)
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.info(f"Query params: {dict(request.query_params)}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Try to log request body
    try:
        body = await request.body()
        if body:
            logger.info(f"Request body: {body.decode('utf-8')[:500]}")
    except:
        pass
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    logger.info(f"=" * 60)
    
    return response

# Store active SSE connections
active_connections = {}


@app.get("/")
async def root():
    """Root endpoint - MCP server info"""
    tools = await list_tools()
    return {
        "name": "EPIC EHR MCP Server",
        "version": "1.0.0",
        "protocol": "mcp",
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in tools
        ]
    }


@app.post("/")
async def root_post(request: Request):
    """Root endpoint POST - handle JSON-RPC at root"""
    try:
        data = await request.json()
        
        # Check if it's a JSON-RPC request
        if data.get("jsonrpc") == "2.0":
            # Forward to MCP endpoint
            return await mcp_jsonrpc_endpoint(request)
        
        # Otherwise return server info
        tools = await list_tools()
        return {
            "name": "EPIC EHR MCP Server",
            "version": "1.0.0",
            "protocol": "mcp",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False
            },
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
        logger.error(f"Error in root POST: {e}")
        return {"error": str(e)}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "transport": "sse"}


async def get_tools_list():
    """Helper function to get tools list"""
    tools = await list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        }
        for tool in tools
    ]


@app.get("/tools")
async def get_tools():
    """Get list of available tools (REST endpoint) - GET"""
    try:
        return await get_tools_list()
    except Exception as e:
        logger.error(f"Error listing tools (GET): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools")
async def post_tools(request: Request):
    """Handle POST to /tools - check if it's JSON-RPC or simple REST"""
    try:
        data = await request.json()
        
        # Check if it's a JSON-RPC request
        if data.get("jsonrpc") == "2.0":
            logger.info("Detected JSON-RPC request at /tools, forwarding to MCP handler")
            # Forward to MCP endpoint handler
            return await mcp_jsonrpc_endpoint(request)
        
        # Otherwise return simple tools list
        return await get_tools_list()
    except Exception as e:
        logger.error(f"Error in POST /tools: {e}")
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
            # Send tools list immediately in MCP format
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
            
            # Send as SSE event
            yield f"data: {json.dumps(tools_data)}\n\n"
            
            logger.info(f"Sent {len(tools)} tools to connection {connection_id}")
            
            # Keep connection alive with heartbeat
            while True:
                await asyncio.sleep(30)
                heartbeat = {
                    "jsonrpc": "2.0",
                    "method": "ping"
                }
                yield f"data: {json.dumps(heartbeat)}\n\n"
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            error_data = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/sse")
async def sse_post_endpoint(request: Request):
    """
    Handle POST requests to SSE endpoint (for MCP protocol)
    Some clients send POST to discover tools
    """
    try:
        # Get tools list
        tools = await list_tools()
        
        tools_list = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in tools
        ]
        
        # Try returning just the array
        return tools_list
        
    except Exception as e:
        logger.error(f"Error in POST /sse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/mcp")
async def mcp_jsonrpc_endpoint(request: Request):
    """
    JSON-RPC 2.0 endpoint for MCP protocol
    This is what Copilot Studio expects!
    
    Handles methods:
    - tools/list: Returns available tools
    - tools/call: Executes a tool
    """
    try:
        data = await request.json()
        
        # Validate JSON-RPC 2.0 format
        jsonrpc = data.get("jsonrpc")
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        if jsonrpc != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: jsonrpc must be '2.0'"
                }
            }
        
        logger.info(f"JSON-RPC request: method={method}, id={request_id}")
        
        # Handle initialize method (MCP protocol handshake)
        if method == "initialize":
            logger.info("Handling MCP initialize request")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "EPIC EHR MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
        
        # Handle tools/list method
        elif method == "tools/list":
            tools = await list_tools()
            tools_list = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
            
            logger.info(f"Returning {len(tools_list)} tools via JSON-RPC")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            }
        
        # Handle tools/call method
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: missing 'name'"
                    }
                }
            
            # Validate access token if provided
            access_token = arguments.get("access_token")
            if access_token:
                token_data = validate_token(access_token)
                if not token_data:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32001,
                            "message": "Invalid access token"
                        }
                    }
            
            # Call the tool
            logger.info(f"Calling tool via JSON-RPC: {tool_name}")
            result = await call_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [r.model_dump() for r in result]
                }
            }
        
        # Method not found
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error: Invalid JSON"
            }
        }
    except Exception as e:
        logger.error(f"Error in JSON-RPC endpoint: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id if 'request_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment or use 8000 as default
    port = int(os.getenv("SSE_PORT", "8000"))
    
    # Run SSE server
    logger.info(f"Starting SSE server on http://0.0.0.0:{port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
