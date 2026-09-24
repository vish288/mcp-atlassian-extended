"""Tests for resource file content and the loader's path guard.

Registration is proved live in ``test_server_assembly.py`` (``list_resources``
plus a read of every URI through the server).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_atlassian_extended.servers.resources import _RESOURCE_FILES, _RESOURCES_DIR, _load


class TestResourceFiles:
    """Verify resource .md files exist and are valid."""

    def test_resources_dir_exists(self) -> None:
        assert Path(_RESOURCES_DIR).is_dir(), f"Resources directory missing: {_RESOURCES_DIR}"

    def test_all_files_exist(self) -> None:
        for filename in _RESOURCE_FILES:
            path = Path(_RESOURCES_DIR) / filename
            assert path.is_file(), f"Missing resource file: {path}"

    def test_load_returns_content(self) -> None:
        for filename in _RESOURCE_FILES:
            content = _load(filename)
            assert len(content) > 100, f"{filename} too short ({len(content)} chars)"

    def test_content_starts_with_heading(self) -> None:
        for filename in _RESOURCE_FILES:
            content = _load(filename)
            assert content.lstrip().startswith("#"), (
                f"{filename} should start with markdown heading"
            )

    def test_no_python_escape_artifacts(self) -> None:
        """Ensure extracted .md files don't contain Python string artifacts."""
        for filename in _RESOURCE_FILES:
            content = _load(filename)
            assert '"""' not in content, f"{filename} contains triple-quote artifact"


class TestLoadSecurity:
    """Verify _load() rejects path traversal attempts."""

    @pytest.mark.parametrize(
        "bad", ["../../../etc/passwd", "subdir/file.md", "subdir\\file.md", ".."]
    )
    def test_rejects(self, bad: str) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            _load(bad)
