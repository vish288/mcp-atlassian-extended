"""Parity tests: the committed derived artifacts must equal their derivation.

If either assertion fails, run ``python scripts/derive_artifacts.py`` and commit
the result — the committed file has drifted from its source.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "derive_artifacts", ROOT / "scripts" / "derive_artifacts.py"
)
assert _spec and _spec.loader
da = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(da)


def test_gemini_extension_matches_server_json():
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    assert (ROOT / "gemini-extension.json").read_text(encoding="utf-8") == da.render_gemini(server)


def test_llms_is_prefix_of_llms_full():
    full = (ROOT / "llms-full.txt").read_bytes()
    assert (ROOT / "llms.txt").read_bytes() == da.build_llms(full)
