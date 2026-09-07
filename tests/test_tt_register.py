"""RNV-TT-REGISTER-GUARD -- the two values rev 27 registered under this app.

Installed 2026-09-07. It exists because of how the fault it fixes was found:
not by anybody reading the file, but by making `engine.brand` importable and
letting a test that had never run say what it had always been going to say.

    GREY_E0 = #e0e0e0 is APP["pressed-light"] in the register, but marked app-ramp
    GREY_F5 = #f5f5f5 is APP["surface-light-3"] in the register, but marked app-ramp

Both values were app-owned neutrals when this application's light half was
wired. rnv-brand rev 27 registered the light surface ladder underneath them
and nothing here noticed, because the only check that compares this app to the
register is guarded with importorskip and rnv-brand is not installable.

The two need OPPOSITE answers, and that is the whole point of this guard:

  * #f5f5f5 is painted by three keys and every one of them is a light window,
    panel or label ground -- which IS what APP["surface-light-3"] is. So the
    constant becomes a register mirror under the register's name.

  * #e0e0e0 is painted by ONE key, the light scrollbar track. The register's
    pressed-light is an INTERACTION STATE and a groove is a resting surface,
    so the ramp name is right and only the classification was wrong. It is a
    declared coincidence, not a mirror -- the same ruling this file already
    carries for GREY_EE / APP_HOVER_LIGHT four lines above it.

These tests do NOT need rnv-brand to be importable. That is deliberate: the
whole failure mode was a check that only runs somewhere else.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

ROOT = Path(__file__).resolve().parent.parent
COLORS = ROOT / 'utils/colors.py'
STYLES = ROOT / 'utils/dialog_styles.py'
LIGHT = DialogStyleManager.LIGHT
DARK = DialogStyleManager.DARK


def test_the_light_ground_is_a_register_mirror_now():
    """#f5f5f5 under the register's own key, classified as the register's."""
    assert colors.APP_SURFACE_LIGHT_3 == '#f5f5f5'
    assert colors.PROVENANCE.get('APP_SURFACE_LIGHT_3') == 'register', (
        'APP_SURFACE_LIGHT_3 is not classified as a register value. It is '
        'APP["surface-light-3"], registered by rnv-brand rev 27.')


def test_the_retired_ramp_name_is_gone():
    """GREY_F5 was the same value under a name that said this app owned it.
    A rename that leaves the old name behind has renamed nothing."""
    src = COLORS.read_text(encoding='utf-8')
    code = '\n'.join(l for l in src.splitlines() if not l.lstrip().startswith('#'))
    assert 'GREY_F5' not in code, 'GREY_F5 still exists in utils/colors.py'
    assert not hasattr(colors, 'GREY_F5')
    assert 'GREY_F5' not in colors.PROVENANCE
    assert 'GREY_F5' not in colors.__all__


@pytest.mark.parametrize('key', ['bg', 'window_bg', 'label_bg'])
def test_every_light_ground_reads_the_register_name(key):
    """Spelling, not only value. A literal or a retired name here cannot
    follow rev 27's ladder the next time it moves."""
    src = STYLES.read_text(encoding='utf-8')
    assert f"'{key}': APP_SURFACE_LIGHT_3," in src, (
        f'{key} does not read APP_SURFACE_LIGHT_3')
    assert LIGHT[key] == '#f5f5f5'


def test_the_light_track_keeps_the_ramp_name():
    """The other half, and the opposite answer. #e0e0e0 IS a register value
    now -- APP["pressed-light"] -- but this key is not a pressed state, so it
    keeps the ramp step. Wiring it to the register's name would claim an
    interaction role for a groove on the strength of a shared byte."""
    assert colors.GREY_E0 == '#e0e0e0'
    assert LIGHT['scrollbar_bg'] == colors.GREY_E0
    src = STYLES.read_text(encoding='utf-8')
    assert "'scrollbar_bg': GREY_E0," in src
    assert colors.PROVENANCE.get('GREY_E0') == 'app-ramp'


def test_the_coincidence_is_declared_with_its_reason():
    """An exemption with no stated reason is indistinguishable from an
    oversight, and the next audit re-litigates it. This asserts the entry
    exists AND that it names the register role it coincides with."""
    from tests import test_brand_mirror as tbm
    assert 'GREY_E0' in tbm.COINCIDENT, (
        'GREY_E0 shares #e0e0e0 with APP["pressed-light"] and is deliberately '
        'NOT mirrored. Undeclared, that reads as a misclassification.')
    entry, why = tbm.COINCIDENT['GREY_E0']
    assert entry == 'APP["pressed-light"]'
    assert len(why) > 80, 'the reason is too short to be a reason'


def test_no_dark_entry_took_either_light_value():
    """Both values belong to the light half. A dark key holding one of them
    would be a mode leak, and this is cheap to assert while we are here."""
    strays = {k: v for k, v in DARK.items()
              if v in ('#f5f5f5', '#e0e0e0')}
    assert not strays, f'dark entries carrying a light surface: {strays}'


def test_the_ramp_is_still_ordered_by_byte():
    """This app names ramp steps by their byte so the ramp reads in order.
    Removing GREY_F5 must not have disturbed the rest."""
    names = re.findall(r'^(GREY_[0-9A-F]{2}): Final',
                       COLORS.read_text(encoding='utf-8'), re.M)
    values = [int(n[5:], 16) for n in names]
    assert values == sorted(values), f'the ramp is out of order: {names}'
    assert 'GREY_F5' not in names


def test_this_guard_can_see_what_it_checks():
    """Guard the guard. Every assertion above walks these two files and the
    two resolved palettes; if any of them stopped resolving, the rest would
    pass over nothing."""
    assert COLORS.exists() and STYLES.exists()
    assert len(LIGHT) > 20 and len(DARK) > 20
    assert len(colors.PROVENANCE) > 20
