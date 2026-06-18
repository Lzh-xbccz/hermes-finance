"""Project path helpers."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / "skills"
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"


def project_path(*parts: str) -> Path:
    """Return an absolute path inside the project root."""

    return PROJECT_ROOT.joinpath(*parts)
