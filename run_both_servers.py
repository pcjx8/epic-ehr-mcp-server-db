"""
Run both WebSocket and SSE servers simultaneously
WebSocket: Port 7777 (for WebSocket clients)
SSE/HTTP: Port 8000 (for Copilot Studio)
"""

import asyncio
import subprocess
import sys
import signal
import os

processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down servers...")
    for proc in processes:
        proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("="*80)
    print("EPIC EHR MCP SERVER - DUAL MODE")
    print("="*80)
    print()
    print("Starting servers:")
    print("  🔌 WebSocket Server: ws://0.0.0.0:7777")
    print("  🌐 SSE/HTTP Server:  http://0.0.0.0:8000")
    print()
    print("Press Ctrl+C to stop both servers")
    print("="*80)
    print()
    
    # Start WebSocket server
    print("🔌 Starting WebSocket server...")
    ws_process = subprocess.Popen(
        [sys.executable, "server.py", "--websocket"],
        cwd=os.path.dirname(__file__)
    )
    processes.append(ws_process)
    
    # Start SSE server
    print("🌐 Starting SSE server...")
    sse_process = subprocess.Popen(
        [sys.executable, "sse_server.py"],
        cwd=os.path.dirname(__file__)
    )
    processes.append(sse_process)
    
    print()
    print("✅ Both servers started!")
    print()
    print("Copilot Studio Configuration:")
    print("  Server URL: http://YOUR_SERVER_IP:8000/sse")
    print("  Or for local: http://localhost:8000/sse")
    print()
    
    # Wait for processes
    try:
        ws_process.wait()
        sse_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
