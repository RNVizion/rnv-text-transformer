"""RNV-STATUS-GUARD -- the family cannot drift back.

A guard rather than a test: this pins the SHAPE of the change, so a later edit
that reintroduces a Bootstrap value, or points a text key back at a fill, fails
here with a message saying which of the two happened and why it matters.
"""

import io
import re
import tokenize
from pathlib import Path

import pytest

from utils import colors
from utils.dialog_styles import DialogStyleManager

RETIRED = {
    "#28a745": "Bootstrap green, retired -- it and the Bootstrap red collapsed "
               "to one olive under deuteranopia at about 4 apart",
    "#ffc107": "Bootstrap amber, retired -- 1.63 on #ffffff and 1.49 on "
               "#f5f5f5 against a 3:1 fill floor",
    "#dc3545": "Bootstrap red, retired with its family",
    "#e56b77": "orphan: derived from #dc3545, which no longer exists",
    "#c82131": "orphan: derived from #dc3545, which no longer exists",
}

SOURCES = SWEPT = ("utils/colors.py", "utils/dialog_styles.py")
LIVE_VALUE = "#926c89"


def _code_only(text: str) -> str:
    """Source with comments and DOCSTRINGS removed -- and nothing else.

    Why this exists: every value these guards forbid is named, in words, in
    the provenance explaining why it was retired. A sweep that cannot tell a
    value being USED from a value being MENTIONED forces the fix to be silence
    about what changed, which is the opposite of what the provenance is for.

    Why it is fussier than it looks: an earlier version dropped every STRING
    token. In Python a colour value IS a string literal -- `X = "#926c89"` --
    so that version removed the uses along with the mentions and the sweep
    could never find anything. It passed on every input, including a file that
    had just put a retired value back. This file's own guard-the-guard is what
    caught it, which is the entire reason for writing guards that check the
    guard can still see.

    So: a STRING token is dropped only when it STARTS a statement -- a
    docstring, or a bare string expression, which is prose either way. A string
    on the right of an assignment, in a dict, or in a call is kept, because
    that is what a value looks like.
    """
    out = []
    # ENCODING behaves like the start of a line for this purpose.
    at_statement_start = True
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and at_statement_start:
                at_statement_start = False
                continue
            if tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENCODING):
                at_statement_start = True
            else:
                at_statement_start = False
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        # Falling back to the raw text can only make a sweep STRICTER, never
        # looser, so it fails safe.
        return text
    return " ".join(out)


@pytest.mark.parametrize("dead", sorted(RETIRED))
def test_no_retired_value_is_live_in_any_source(dead):
    for rel in SOURCES:
        text = Path(rel).read_text(encoding="utf-8")
        assert dead not in _code_only(text), (
            f"{rel} uses {dead} again -- {RETIRED[dead]}")


@pytest.mark.parametrize("dead", sorted(RETIRED))
def test_no_retired_value_is_reachable_as_a_constant(dead):
    live = {v for k, v in vars(colors).items()
            if isinstance(v, str) and v.startswith("#")}
    assert dead not in live, f"{dead} is back as a constant -- {RETIRED[dead]}"


@pytest.mark.parametrize("key", ["success", "warning", "error"])
@pytest.mark.parametrize("is_dark", [True, False])
def test_a_status_key_never_carries_a_fill(key, is_dark):
    """The specific wrong migration, named so it cannot be made by accident.

    Swapping the value while leaving the key pointed at a fill is the change
    this pass exists NOT to make: it takes these six readings from one failure
    to six. If someone repoints these keys at STATUS_SUCCESS / _WARNING /
    _ERROR, this is the line that stops it.
    """
    fills = {colors.STATUS_SUCCESS, colors.STATUS_WARNING, colors.STATUS_ERROR}
    value = DialogStyleManager.get_colors(is_dark)[key]
    assert value not in fills, (
        f"{'dark' if is_dark else 'light'} '{key}' is painted with a FILL "
        f"({value}). Fills sit at L* 48-59 and cannot reach 4.5:1 as text on "
        f"either ground; this key is read only in `color:` declarations.")


def test_the_two_spellings_did_not_come_back():
    """The register recorded that this one colour was derived independently
    under TWO identifiers across three applications -- STATUS_ERROR_LIGHT here
    and in the picker, STATUS_ERROR_TEXT_LIGHT in the palette manager. One
    name now, and the old one must not reappear alongside it."""
    for rel in SOURCES:
        text = Path(rel).read_text(encoding="utf-8")
        assert not re.search(r"\bSTATUS_ERROR_LIGHT\b", _code_only(text)), (
            f"{rel} reintroduced STATUS_ERROR_LIGHT; the name is "
            f"STATUS_ERROR_TEXT_LIGHT")


def test_the_six_text_variants_are_all_exported():
    """A value the package does not export is a value the next application
    cannot mirror, which is how a fleet ends up with six spellings."""
    import utils
    for role in ("SUCCESS", "WARNING", "ERROR"):
        for suffix in ("_TEXT", "_TEXT_LIGHT"):
            name = f"STATUS_{role}{suffix}"
            assert hasattr(utils, name), f"utils does not export {name}"
            assert name in utils.__all__, f"{name} is missing from utils.__all__"


def test_this_guard_can_still_see():
    """Guard the guard, and it has already earned its place.

    _code_only exists so provenance can name a retired value without failing
    the sweep that forbids it. An earlier version dropped EVERY string token,
    which in Python also drops the values -- so the sweep above could never
    find anything and passed on every input, including a file that had just
    put a retired value back. This assertion is what caught that.
    """
    src = Path(SWEPT[0]).read_text(encoding="utf-8")
    code = _code_only(src)
    assert len(code) > 2000, "the tokeniser returned almost nothing"
    assert LIVE_VALUE in code, (
        f"the code-only sweep cannot see {LIVE_VALUE}, which is definitely a "
        f"value in {SWEPT[0]}. The sweep for retired values is therefore "
        f"vacuous and would pass on anything.")
