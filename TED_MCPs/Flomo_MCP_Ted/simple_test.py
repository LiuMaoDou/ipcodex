import json
import sys

# Test if the server responds to basic MCP messages
test_message = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}

# Read from stdin and respond
try:
    response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "flomo-test", "version": "0.1.0"}
        }
    }
    print(json.dumps(response))
    sys.stdout.flush()
    print("MCP Server test successful!", file=sys.stderr)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)