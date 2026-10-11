"""Filesystem containment for attachment paths (AT-R06 upload, AT-R07 download).

Lives beside ``config.py`` rather than under ``servers/`` because the Jira client
needs it and clients must not import ``servers``.
"""

from __future__ import annotations

from pathlib import Path


def _inside(root: Path, candidate: Path, *, what: str, env: str) -> Path:
    """Resolve *candidate* and return it, or raise ``ValueError``.

    *root* must already be resolved. Containment is checked against the *resolved*
    candidate — so a symlink that points outside the root is rejected — and before
    existence, so a path outside the root never reveals whether it exists. No
    component of the path *below* the root may start with a dot; the root itself
    may be a dot-directory. *what* names the parameter and *env* the variable to
    set, both for the message.
    """
    noun = "upload directory" if "UPLOAD" in env else "download directory"
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        msg = (
            f"{what} resolves outside the {noun} {root}: {resolved}. "
            f"Set {env} to a directory that contains the file."
        )
        raise ValueError(msg)
    for component in resolved.relative_to(root).parts:
        if component.startswith("."):
            msg = (
                f"{what} points at a hidden file or directory ({component}); "
                "dotfiles and dot-directories are never uploaded."
            )
            raise ValueError(msg)
    return resolved
