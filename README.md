# Godot LSP MCP Server

An MCP server that provides GDScript diagnostics by connecting to the Godot Editor's LSP.

## Features

- **validate_gdscript**: Validate GDScript files and get diagnostics (errors, warnings) from the running Godot Editor.

## Prerequisites

- Godot Engine 4.5+ (running with the project open)
- Python 3.13 or higher

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/madewithscience/godot-lsp-mcp.git
   cd godot-lsp-mcp
   ```

## Configuration

```shell
python3 server.py --config
```
Should output something like:

```json
{
  "mcpServers": {
    "godot-lsp-mcp": {
      "command": "/path/to/python3",
      "args": [
        "/path/to/dir/server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/dir"
      }
    }
  }
}
```

## Godot Project Settings

```toml
[debug]

gdscript/warnings/untyped_declaration=1
gdscript/warnings/unsafe_property_access=1
gdscript/warnings/unsafe_method_access=1
gdscript/warnings/unsafe_cast=1
gdscript/warnings/unsafe_call_argument=1
```


## Basic demo with Junie

[![Watch the video](https://img.youtube.com/vi/ejFDH4nN9NM/maxresdefault.jpg)](https://youtu.be/ejFDH4nN9NM)

