"""
Contrast pairing guard.

The rest of the suite asserts hex EQUALITY -- DARK["accent"] == "#d2bc93".
That cannot catch a legible colour placed on the wrong ground, which is how
eight failing gold pairings survived every previous audit: every value was
correct, every pairing was not.

This walks the generated stylesheets, resolves each `color` against the
background it actually renders on, and applies the WCAG floor.

Exceptions below are recorded decisions, not silence. Each one names why.
"""
from __future__ import annotations

import re

import pytest

from utils.dialog_styles import DialogStyleManager

TEXT_FLOOR = 4.5
HEX = re.compile(r'#[0-9a-fA-F]{6,8}$')
COMPONENTS = ('splitter', 'menu', 'table', 'tab', 'spinbox', 'slider',
              'list', 'progressbar', 'tree')

# (theme, foreground, background) -> why it may sit below the floor
ACCEPTED = {
    # WCAG 1.4.3 exempts text in an inactive user interface component.
    ('LIGHT', '#aaaaaa', '#e8e8e8'): 'disabled control text -- WCAG-exempt',
    ('LIGHT', '#aaaaaa', '#f5f5f5'): 'disabled control text -- WCAG-exempt',
    ('DARK',  '#555555', '#333333'): 'disabled control text -- WCAG-exempt',
    ('DARK',  '#555555', '#1a1a1a'): 'disabled control text -- WCAG-exempt',
    # Pre-existing, unrelated to gold: unselected dark tab labels.
    ('DARK',  '#888888', '#2a2a2a'): 'unselected tab label -- 4.05:1',
}


def _luminance(value: str) -> float:
    h = value.lstrip('#')
    if len(h) == 8:                       # Qt #AARRGGBB
        h = h[2:]
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    chans = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
             for c in chans]
    return 0.2126 * chans[0] + 0.7152 * chans[1] + 0.0722 * chans[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _rules(css: str):
    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        selector = ' '.join(match.group(1).split())
        props = {}
        for decl in match.group(2).split(';'):
            if ':' in decl:
                key, _, val = decl.partition(':')
                props[key.strip()] = val.strip()
        yield selector, props


def _pairs(is_dark: bool):
    colors = DialogStyleManager.get_colors(is_dark)
    css = DialogStyleManager.get_extended_stylesheet(
        is_dark, 'Arial', *COMPONENTS)
    for selector, props in _rules(css):
        fg = props.get('color')
        if not fg or not HEX.match(fg):
            continue
        bg = props.get('background-color') or props.get('background')
        if not bg or not HEX.match(bg):
            bg = colors['bg']             # inherits the dialog surface
        yield selector, fg.lower(), bg.lower()


@pytest.mark.parametrize('is_dark,theme', [(False, 'LIGHT'), (True, 'DARK')])
def test_text_pairs_meet_aa(is_dark, theme):
    """Every text colour clears 4.5:1 on the ground it renders on."""
    failures = []
    for selector, fg, bg in _pairs(is_dark):
        if (theme, fg, bg) in ACCEPTED:
            continue
        ratio = contrast(fg, bg)
        if ratio < TEXT_FLOOR:
            failures.append(f'{theme} {selector}: {fg} on {bg} = {ratio:.4f}:1')
    assert not failures, (
        'text below AA 4.5:1 --\n  ' + '\n  '.join(sorted(set(failures)))
        + '\n\nIf one of these is intentional, add it to ACCEPTED with a reason.')


@pytest.mark.parametrize('is_dark,theme', [(False, 'LIGHT'), (True, 'DARK')])
def test_accepted_entries_are_still_real(is_dark, theme):
    """An ACCEPTED entry that no longer occurs is stale and should be removed."""
    seen = {(theme, fg, bg) for _, fg, bg in _pairs(is_dark)}
    stale = [k for k in ACCEPTED if k[0] == theme and k not in seen]
    assert not stale, f'stale ACCEPTED entries for {theme}: {stale}'


def test_light_mode_has_exactly_two_golds():
    """One ruled value plus one derivative. A third means a role went unshared."""
    light = DialogStyleManager.get_colors(False)
    golds = {light[k].lower() for k in
             ('accent', 'accent_hover', 'accent_pressed', 'accent_ink',
              'border_focus', 'tooltip_border', 'info', 'selection_bg',
              'output_text_color', 'line_number_current_fg')}
    assert len(golds) == 2, f'expected 2 light golds, found {len(golds)}: {sorted(golds)}'


def test_deep_gold_serves_both_its_roles():
    """The one derivative must work as a white-bearing fill AND as text."""
    light = DialogStyleManager.get_colors(False)
    deep = light['accent_ink']
    assert light['accent_hover'] == deep, 'hover and ink must share the derivative'
    assert contrast('#ffffff', deep) >= TEXT_FLOOR, 'white must clear on the deep gold'
    for surface in ('#f5f5f5', '#eeeeee', '#e8e8e8'):
        ratio = contrast(deep, surface)
        assert ratio >= TEXT_FLOOR, f'deep gold on {surface} = {ratio:.4f}:1'


def test_dark_mode_keeps_one_gold_for_text():
    """Dark has headroom everywhere; accent_ink must not diverge there."""
    dark = DialogStyleManager.get_colors(True)
    assert dark['accent_ink'] == dark['accent']
