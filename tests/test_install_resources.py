"""AN INSTALLED COPY CARRIES resources/ (#97 A, 2026-10-24).

THE FAULT IT KEEPS AWAY. `pip install .` built a wheel with no font, icons,
button images or background in it. The hatch wheel target listed the
packages core, ui, utils and cli and force-included the main script, and
nothing named resources/, which is not inside any of those packages. The
installed app then looked for site-packages/resources/, found no font and
no images, fell back to Arial, and could not offer Image mode.

WHAT IT HOLDS, by reading pyproject.toml (no build):
  1. every file under resources/ goes into the wheel, at resources/<path>,
     through the wheel's packages or its force-include table;
  2. the app looks for resources/ beside utils/, and utils/ installs at the
     top of the wheel, so that is where the files land.

A wheel built from this repository lists every one of them under resources/.
"""
from __future__ import annotations

import tomllib
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "resources"


def _wheel_target() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["tool"]["hatch"]["build"]["targets"]["wheel"]


def _files_under(folder: Path) -> set[str]:
    return {
        p.relative_to(ROOT).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def _wheel_path(source: str) -> str | None:
    """Where hatch puts a repository file in the wheel, or None if it leaves it out."""
    target = _wheel_target()
    src = PurePosixPath(source)
    for package in target.get("packages", []):
        if src.is_relative_to(PurePosixPath(package)):
            return source
    for from_path, to_path in target.get("force-include", {}).items():
        base = PurePosixPath(from_path)
        if src == base or src.is_relative_to(base):
            return (PurePosixPath(to_path) / src.relative_to(base)).as_posix()
    return None


def test_every_resource_file_goes_into_the_wheel_at_its_own_path():
    on_disk = _files_under(RESOURCES)
    assert on_disk, "resources/ is empty, so this check proved nothing"
    placed = {source: _wheel_path(source) for source in on_disk}
    missing = sorted(s for s, dest in placed.items() if dest is None)
    assert not missing, f"left out of an installed copy: {missing}"
    moved = sorted(s for s, dest in placed.items() if dest != s)
    assert not moved, f"installed somewhere the app does not look: {moved}"


def test_the_app_looks_for_resources_beside_utils():
    from utils import config
    utils_dir = Path(config.__file__).resolve().parent
    assert "utils" in _wheel_target().get("packages", [])
    assert config.RESOURCES_DIR.resolve() == utils_dir.parent / "resources"
    for folder in (config.BUTTON_IMAGES_DIR, config.BACKGROUND_IMAGES_DIR,
                   config.FONTS_DIR, config.ICONS_DIR):
        assert folder.resolve().is_relative_to(config.RESOURCES_DIR.resolve())
        assert folder.is_dir()
