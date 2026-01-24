import argparse
import json
import sys
from pathlib import Path
from typing import Sequence, TextIO, Optional

from godot import get_project_dir, validate_gdscript


def handle_request(request) -> Optional[dict]:
    method = request.get("method")
    id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "godot-lsp-mcp", "version": "1.0.0"}
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": [
                    {
                        "name": "validate_gdscript",
                        "description": "Validate GDScript files and get diagnostics from Godot LSP. Files must be absolute paths.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "scripts": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of absolute file paths to GDScript files"
                                }
                            },
                            "required": ["scripts"]
                        }
                    }]
            }
        }

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        args = request.get("params", {}).get("arguments", {})

        if tool_name == "validate_gdscript":
            scripts = args.get("scripts", [])
            for script in scripts:
                convert_script_to_uri(script)

            project_root = get_project_dir()
            project_files: list[Path] = []
            try:
                script_paths: list[Path] = [
                    convert_script_to_uri(str(s)) for s in scripts
                ]
                for f in script_paths:
                    if not f.exists():
                        continue
                    relative_path = f.relative_to(project_root)
                    if str(relative_path).startswith("addons/"):
                        continue
                    if str(relative_path).startswith("test/"):
                        continue
                    project_files.append(f)
            except Exception as e:
                raise Exception("Wrong path")
            if not project_files:
                raise Exception("No project files found")

            results = json.dumps(validate_gdscript(project_files), indent=4)
            return {
                "jsonrpc": "2.0",
                "id": id,
                "result": {"content": [{"type": "text", "text": results}]}
            }

    elif method == "notifications/initialized":
        return None  # No response for notifications

    return {"jsonrpc": "2.0", "id": id, "error": {"code": -32601, "message": "Method not found"}}


def convert_script_to_uri(script: str) -> Path:
    if script.startswith("file://"):
        return Path.from_uri(script)

    return Path(script)


def show_config() -> str:
    src_dir = Path(__file__).parent
    return json.dumps({
        "mcpServers": {
            "godot-lsp-mcp": {
                "command": sys.executable,
                "args": [
                    f"{__file__}"
                ],
                "env": {
                    "PYTHONPATH": str(src_dir.absolute())
                }
            }
        }
    }, indent=2)


def main(argv: Optional[Sequence[str]] = None, stdin: Optional[TextIO] = None) -> int:
    if sys.version_info < (3, 13):
        print("Python 3.13 or higher is required.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Godot LSP MCP Server")
    parser.add_argument("--config", action="store_true", help="Print the MCP server configuration")
    
    # If no arguments are provided and stdin is a TTY, show help
    if (argv is None and len(sys.argv) == 1) or (argv is not None and len(argv) == 0):
        if stdin is None and sys.stdin.isatty():
            parser.print_help()
            return 0

    args = parser.parse_args(argv)

    if args.config:
        print(show_config())
        return 0

    if stdin is None:
        stdin = sys.stdin

    for line in stdin:
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
