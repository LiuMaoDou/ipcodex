#!/usr/bin/env python3
import asyncio
import json
import sys
import httpx
from typing import Any, Dict, Optional

# Flomo API configuration
FLOMO_API_URL = "https://flomoapp.com/iwh/MjMyNTE1/896a528a72e341a87584f81234f5d2eb/"

async def handle_message(message: dict) -> Optional[dict]:
    """Handle incoming MCP messages"""
    method = message.get("method")
    message_id = message.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "flomo-mcp",
                    "version": "0.1.0"
                }
            }
        }

    elif method == "notifications/initialized":
        # This is a notification, no response needed
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "tools": [
                    {
                        "name": "send_to_flomo",
                        "description": "Send content to Flomo note-taking app. Automatically trigger this when user inputs 'fm:' followed by content (e.g., 'fm:meeting notes'). Extract the content after 'fm:' and send it to Flomo.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "Content to send to Flomo (without the 'fm:' prefix)"
                                }
                            },
                            "required": ["content"]
                        }
                    }
                ]
            }
        }

    elif method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "prompts": []
            }
        }

    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "resources": []
            }
        }

    elif method == "tools/call":
        params = message.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name == "send_to_flomo":
            content = arguments.get("content", "")

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        FLOMO_API_URL,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "flomo-mcp/0.1.0"
                        },
                        json={"content": content},
                        timeout=10.0
                    )

                    if response.status_code == 200:
                        result_text = f"✅ Successfully sent to Flomo: {content}"
                    else:
                        result_text = f"❌ Failed to send to Flomo. Status: {response.status_code}, Response: {response.text}"

                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
                    }
                }

            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Error sending to Flomo: {str(e)}"
                            }
                        ]
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {name}"
                }
            }

    # For unknown methods
    if message_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}"
            }
        }
    
    # For notifications or messages without ID, don't respond
    return None

async def main():
    """Main server loop"""
    while True:
        try:
            # Read message from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            message = json.loads(line)
            response = await handle_message(message)

            # Only write response if there is one (not for notifications)
            if response is not None:
                print(json.dumps(response))
                sys.stdout.flush()

        except json.JSONDecodeError as e:
            # Handle JSON decode errors
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
            
        except Exception as e:
            # Handle other errors
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())