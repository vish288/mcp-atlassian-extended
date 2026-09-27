#!/usr/bin/env python3
"""Derive the hand-free artifacts from their single sources of truth.

- ``gemini-extension.json`` is built from ``server.json`` (env-var settings and
  the version), so the Gemini CLI install manifest never drifts from the MCP
  registry manifest.
- ``llms.txt`` is the documented prefix of ``llms-full.txt`` (everything before
  the "Environment Variables" section).

Both files stay committed (Gemini installs from the repo; llms.txt is fetched
from main). The release workflow runs this after the version bump so the
generated files carry the new version, and ``test_derived_artifacts.py`` fails
if either committed file drifts from what this produces.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# llms.txt is llms-full.txt up to (but not including) this section heading.
LLMS_CUT = b"\n## Environment Variables"


def build_gemini(server: dict) -> dict:
    """Map server.json onto the Gemini extension manifest shape."""
    pkg = server["packages"][0]
    identifier = pkg["identifier"]
    return {
        "name": identifier,
        "version": server["version"],
        "description": server["description"],
        "mcpServers": {
            identifier: {"command": "uvx", "args": [identifier]},
        },
        "settings": [
            {
                "name": env["name"],
                "description": env["description"],
                "required": env["isRequired"],
                "sensitive": env["isSecret"],
            }
            for env in pkg["environmentVariables"]
        ],
    }


def render_gemini(server: dict) -> str:
    """gemini-extension.json contents for the given server.json data."""
    return json.dumps(build_gemini(server), indent=2) + "\n"


def build_llms(full: bytes) -> bytes:
    """The llms.txt prefix of the given llms-full.txt bytes."""
    return full[: full.index(LLMS_CUT)]


def main() -> None:
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    (ROOT / "gemini-extension.json").write_text(render_gemini(server), encoding="utf-8")
    full = (ROOT / "llms-full.txt").read_bytes()
    (ROOT / "llms.txt").write_bytes(build_llms(full))


if __name__ == "__main__":
    main()
