"""
tests/test_project_urls.py
==========================
pyproject's [project.urls] point at this repository (#97 A).

They pointed at github.com/RNVSoftware/..., an organization the
repository is not in. The README's clone command names the real one, so
the two are held to each other.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _clone_url() -> str:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    match = re.search(r"git clone (https://github\.com/\S+?)(?:\.git)?\s", readme)
    assert match, "README has no git clone command"
    return match.group(1)


def test_readme_clones_the_rnvizion_repository():
    assert _clone_url() == "https://github.com/RNVizion/rnv-text-transformer"


def test_project_urls_point_at_the_repository():
    urls = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["urls"]
    base = _clone_url()
    assert urls["Homepage"] == base
    assert urls["Repository"] == base
    assert urls["Issues"] == base + "/issues"
