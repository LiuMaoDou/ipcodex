# Flomo MCP Server

A Model Context Protocol (MCP) server for integrating with the Flomo note-taking app. This server allows you to send content to Flomo directly from Claude Desktop by using the `fm:` prefix.

## Features

- Send notes to Flomo with the `fm:xxx` command format
- Seamless integration with Claude Desktop on Windows
- Automatic content formatting for Flomo API

## Installation

1. Navigate to the project directory:
```bash
cd TED_MCPs/Flomo_MCP_Ted
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration for Claude Desktop

To integrate this MCP server with Claude Desktop on Windows, you need to modify the Claude Desktop configuration file.

### Step 1: Locate Claude Desktop Config

The Claude Desktop configuration file is typically located at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Step 2: Add MCP Server Configuration

Add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "flomo": {
      "command": "python",
      "args": [
        "D:\\Code\\ByteAce\\TED_MCPs\\Flomo_MCP_Ted\\flomo_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "D:\\Code\\ByteAce\\TED_MCPs\\Flomo_MCP_Ted"
      }
    }
  }
}
```

**Note**: Replace `D:\\Code\\ByteAce\\TED_MCPs\\Flomo_MCP_Ted\\flomo_mcp.py` with the actual absolute path to your `flomo_mcp.py` file.

### Step 3: Restart Claude Desktop

After updating the configuration file, restart Claude Desktop for the changes to take effect.

## Usage

Once configured, you can use the Flomo MCP server in Claude Desktop by typing:

```
fm:Your note content here
```

For example:
- `fm:Meeting notes for today #work`
- `fm:Great idea about the project #brainstorm`
- `fm:Remember to buy groceries #personal`

The server will automatically call the Flomo API and send your content to your Flomo account.

## API Configuration

The server is currently configured to use the Flomo API endpoint:
```
https://flomoapp.com/iwh/MjMyNTE1/896a528a72e341a87584f81234f5d2eb/
```

If you need to modify the API endpoint or add authentication, edit the `FLOMO_API_URL` variable in `flomo_mcp.py`.

## Troubleshooting

1. **Server not starting**: Check that Python and all dependencies are properly installed
2. **API errors**: Verify your Flomo API endpoint is correct and accessible
3. **Configuration issues**: Ensure the path in `claude_desktop_config.json` is correct and uses forward slashes or escaped backslashes

## Development

To modify the server behavior:

1. Edit `flomo_mcp.py` to customize the API interaction
2. Update `requirements.txt` if you add new dependencies
3. Restart Claude Desktop to reload the server

## License

MIT License