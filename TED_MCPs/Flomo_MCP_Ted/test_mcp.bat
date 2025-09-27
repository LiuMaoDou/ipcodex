@echo off
echo Testing Flomo MCP Server...
echo.
echo Sending test message to MCP server:
echo {"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}

C:\ProgramData\anaconda3\python.exe flomo_mcp.py < test_input.txt

pause