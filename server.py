"""
EPIC EHR MCP Server with Database Persistence
Production-ready server with OAuth 2.0 authentication
"""

import asyncio
import logging
import json
import os
from datetime import datetime, date
from typing import Optional
import uuid

import websockets
from websockets.server import serve
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Database imports
from database import init_database, get_db_session
from models import Patient, Provider, Appointment, Medication, Allergy, LabResult, VitalSign
from sqlalchemy import or_, and_

# Authentication imports
from auth import authenticate_client, validate_token, register_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("epic-ehr-mcp-server")

# Initialize MCP server
app = Server("epic-ehr-mcp-server")

# Initialize database on startup
init_database()
logger.info("Database initialized")



@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available EHR tools"""
    return [
        # OAuth 2.0 Authentication
        Tool(
            name="authenticate",
            description="Authenticate using OAuth 2.0 Client Credentials (client_id, client_secret, app_id)",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "OAuth client ID"},
                    "client_secret": {"type": "string", "description": "OAuth client secret"},
                    "app_id": {"type": "string", "description": "Application ID"}
                },
                "required": ["client_id", "client_secret", "app_id"]
            }
        ),
        Tool(
            name="register_client",
            description="Register a new OAuth client application",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "Application identifier"},
                    "app_name": {"type": "string", "description": "Application name"},
                    "role": {"type": "string", "description": "Role: doctor, nurse, patient, admin, system"},
                    "scopes": {"type": "array", "items": {"type": "string"}, "description": "List of scopes"},
                    "description": {"type": "string", "description": "Optional description"},
                    "contact_email": {"type": "string", "description": "Optional contact email"}
                },
                "required": ["app_id", "app_name", "role", "scopes"]
            }
        ),
        Tool(
            name="validate_token",
            description="Validate OAuth access token",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "Access token to validate"}
                },
                "required": ["access_token"]
            }
        ),
        # Patient Management
        Tool(
            name="get_patient",
            description="Get patient by MRN",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string", "description": "Patient MRN"}
                },
                "required": ["access_token", "mrn"]
            }
        ),
        Tool(
            name="search_patients",
            description="Search patients by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "search_term": {"type": "string", "description": "Search term"}
                },
                "required": ["access_token", "search_term"]
            }
        ),
        Tool(
            name="create_patient",
            description="Create new patient",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "dob": {"type": "string", "description": "Date of birth (YYYY-MM-DD)"},
                    "gender": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"}
                },
                "required": ["access_token", "first_name", "last_name", "dob"]
            }
        ),
        # Appointments
        Tool(
            name="get_appointments",
            description="Get patient appointments",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"},
                    "status": {"type": "string"}
                },
                "required": ["access_token", "mrn"]
            }
        ),
        Tool(
            name="schedule_appointment",
            description="Schedule new appointment",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"},
                    "provider_npi": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["access_token", "mrn", "provider_npi", "date", "time"]
            }
        ),
        # Medications
        Tool(
            name="get_medications",
            description="Get patient medications",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"}
                },
                "required": ["access_token", "mrn"]
            }
        ),
        Tool(
            name="prescribe_medication",
            description="Prescribe new medication",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"},
                    "medication_name": {"type": "string"},
                    "dosage": {"type": "string"},
                    "frequency": {"type": "string"},
                    "refills": {"type": "number"}
                },
                "required": ["access_token", "mrn", "medication_name", "dosage", "frequency"]
            }
        ),
        # Lab Results
        Tool(
            name="get_lab_results",
            description="Get patient lab results",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"}
                },
                "required": ["access_token", "mrn"]
            }
        ),
        # Vital Signs
        Tool(
            name="get_vital_signs",
            description="Get patient vital signs",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"}
                },
                "required": ["access_token", "mrn"]
            }
        ),
        Tool(
            name="record_vital_signs",
            description="Record new vital signs",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"},
                    "systolic_bp": {"type": "number"},
                    "diastolic_bp": {"type": "number"},
                    "heart_rate": {"type": "number"},
                    "temperature": {"type": "number"}
                },
                "required": ["access_token", "mrn"]
            }
        ),
        # Allergies
        Tool(
            name="get_allergies",
            description="Get patient allergies",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_token": {"type": "string", "description": "OAuth access token"},
                    "mrn": {"type": "string"}
                },
                "required": ["access_token", "mrn"]
            }
        )
    ]



@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        logger.info(f"Tool called: {name}")
        
        # Import tool functions
        from tools import (
            get_patient_tool, search_patients_tool, create_patient_tool,
            get_appointments_tool, schedule_appointment_tool,
            get_medications_tool, prescribe_medication_tool,
            get_lab_results_tool, get_vital_signs_tool, record_vital_signs_tool,
            get_allergies_tool
        )
        
        # OAuth Authentication
        if name == "authenticate":
            result = authenticate_client(**arguments)
        elif name == "register_client":
            result = register_client(**arguments)
        elif name == "validate_token":
            result = validate_token(arguments.get("access_token"))
        # All other tools require token validation
        else:
            access_token = arguments.get("access_token")
            if not access_token:
                raise ValueError("Access token required")
            
            # Validate token
            token_validation = validate_token(access_token)
            if not token_validation.get("valid"):
                raise ValueError(f"Invalid token: {token_validation.get('error')}")
            
            # Route to appropriate tool
            if name == "get_patient":
                result = await get_patient_tool(**arguments)
            elif name == "search_patients":
                result = await search_patients_tool(**arguments)
            elif name == "create_patient":
                result = await create_patient_tool(**arguments)
            elif name == "get_appointments":
                result = await get_appointments_tool(**arguments)
            elif name == "schedule_appointment":
                result = await schedule_appointment_tool(**arguments)
            elif name == "get_medications":
                result = await get_medications_tool(**arguments)
            elif name == "prescribe_medication":
                result = await prescribe_medication_tool(**arguments)
            elif name == "get_lab_results":
                result = await get_lab_results_tool(**arguments)
            elif name == "get_vital_signs":
                result = await get_vital_signs_tool(**arguments)
            elif name == "record_vital_signs":
                result = await record_vital_signs_tool(**arguments)
            elif name == "get_allergies":
                result = await get_allergies_tool(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        logger.info(f"Tool {name} completed successfully")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
        error_result = {"status": "error", "message": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# WebSocket handler
async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data.get('method', 'unknown')}")
                
                # Handle MCP protocol messages
                if data.get("method") == "tools/list":
                    tools = await list_tools()
                    response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {"tools": [tool.model_dump() for tool in tools]}
                    }
                    await websocket.send(json.dumps(response))
                
                elif data.get("method") == "tools/call":
                    params = data.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    result = await call_tool(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {"content": [r.model_dump() for r in result]}
                    }
                    await websocket.send(json.dumps(response))
                
                else:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    }
                    await websocket.send(json.dumps(error_response))
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id") if 'data' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                await websocket.send(json.dumps(error_response))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")


async def start_websocket_server(host: str = "0.0.0.0", port: int = 7777):
    """Start WebSocket server"""
    logger.info(f"Starting EPIC EHR MCP Server on ws://{host}:{port}")
    async with serve(websocket_handler, host, port):
        await asyncio.Future()  # Run forever


async def start_stdio_server():
    """Start stdio server for local MCP connections"""
    logger.info("Starting EPIC EHR MCP Server (stdio)...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--websocket":
        # Run as WebSocket server
        host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 7777
        asyncio.run(start_websocket_server(host, port))
    else:
        # Run as stdio server (default for MCP)
        asyncio.run(start_stdio_server())
