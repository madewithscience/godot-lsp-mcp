import io
import json

from godot import get_project_dir
from server import main


def test_get_project_dir():
    project_dir = get_project_dir()
    assert project_dir.exists()


def test_diagnostics_content(capsys):
    project_dir = get_project_dir()
    test_file = project_dir / "diagnostics_test.gd"
    assert test_file.exists()

    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "validate_gdscript", "arguments": {"scripts": [str(test_file.resolve())]}}},
    ]
    fake_stdin = io.StringIO("\n".join(json.dumps(r) for r in requests))

    main(argv=[], stdin=fake_stdin)

    captured = capsys.readouterr()

    response = json.loads(captured.out.strip())
    content = response["result"]["content"]
    results = json.loads(content[0]["text"])
    diagnostics = results[0]["diagnostics"]

    untyped_warnings = [d for d in diagnostics if "(UNTYPED_DECLARATION)" in d["message"]]

    assert len(untyped_warnings) >= 3

    messages = [d["message"] for d in untyped_warnings]
    assert any('Variable "missing_type" has no static type.' in m for m in messages)
    assert any('Function "do_nothing()" has no static return type.' in m for m in messages)
    assert any('Variable "something" has no static type.' in m for m in messages)



