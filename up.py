#!/usr/bin/env python3
"""
Two golds per mode for RNVizion/rnv-text-transformer.
=====================================================
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Run from the repository root:

    python apply_transformer_two_golds.py                # apply and verify
    python apply_transformer_two_golds.py --verify-only
    python apply_transformer_two_golds.py --finish       # verify, then remove me

WHAT THIS CHANGES

1. GOLD_PRESSED stops being a third gold.

   The brand registers two golds and derives the rest when needed. Each
   mode gets the registered gold and ONE derivative; every other gold role
   reuses one of those two. Light already worked that way here --
   BRAND_DARK_GOLD_PRESSED is the accent itself. Dark did not: it carried
   BRAND_GOLD, GOLD_HOVER and GOLD_PRESSED, three values.

       GOLD_PRESSED = lighten(BRAND_GOLD, -23)   ->  GOLD_PRESSED = BRAND_GOLD

   The third gold, #bba57c, had exactly one job: a 2px tab underline, in
   ui/about_dialog.py and utils/dialog_styles.py. Light draws that same
   underline with the base accent. On the dark hover ground #3a3a3a the
   underline goes 4.7589 -> 6.1503, both clearing the 3.0 component floor,
   so this is a count fix rather than a contrast fix.

   Nothing is broken today. The reason to do it is that a third gold is
   how rnv-color-picker kept #c4a458 unnoticed for months: a tint of a gold
   that had already been retired, still rendering on one key, with nothing
   anywhere counting. A contrast check cannot see that -- an extra gold is
   usually perfectly legible.

2. The duplicate 'accent_ink' key, once in each theme dict.

   Both dicts list it twice with the same value, so today it changes
   nothing and the second silently wins. The day the two lines differ, the
   first becomes dead code that reads as live.

3. tests/test_brand_mirror.py gains the count as a guard, so the rule
   holds without anyone remembering it: two golds per mode, the registered
   one must be one of them, pressed returns to the accent in both modes,
   and no theme key may be defined twice.

WHAT THIS DELIBERATELY DOES NOT CHANGE

* Every button transition. Rest, hover and pressed keep their exact
  colours in both modes -- this touches one 2px underline and nothing
  else. The gold dialog scheme and the plain main-window scheme both stay
  as they are.
* GOLD_HOVER, which is dark mode's one derivative and stays derived.
* Any light-mode value. Light already satisfied the rule.
"""

from __future__ import annotations

import argparse
import ast
import base64
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
COLORS = REPO / "utils" / "colors.py"
STYLES = REPO / "utils" / "dialog_styles.py"
GUARD = REPO / "tests" / "test_brand_mirror.py"

RETIRED_GOLD = "#bba57c"
TOOL_MARKER = "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP"
GUARD_MARKER = "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN"
GUARD_BLOCK_B64 = (
    "CgojIOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkAojIFRXTyBHT0xEUyBQRVIgTU9ERQojIOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
    "kOKVkOKVkOKVkOKVkAojCiMgUk5WLUdPTEQtR1VBUkQtRklMRS1OQU1FUy1SRVRJUkVE"
    "LVZBTFVFUy1CWS1ERVNJR04KIwojIFRoZSBicmFuZCByZWdpc3RlcnMgdHdvIGdvbGRz"
    "IC0tIEJSQU5EX0dPTEQgZm9yIGRhcmsgZ3JvdW5kcywKIyBCUkFORF9EQVJLX0dPTEQg"
    "Zm9yIGxpZ2h0IC0tIGFuZCBkZXJpdmVzIHRoZSByZXN0IHdoZW4gbmVlZGVkLiAiV2hl"
    "bgojIG5lZWRlZCIgaXMgbG9hZC1iZWFyaW5nOiBhIG1vZGUgZ2V0cyBPTkUgZGVyaXZh"
    "dGl2ZSwgYW5kIGV2ZXJ5IG90aGVyIGdvbGQKIyByb2xlIHJldXNlcyB0aGUgYWNjZW50"
    "IG9yIHRoYXQgZGVyaXZhdGl2ZS4gRm91ciB2YWx1ZXMgYWNyb3NzIHRoZSBhcHAsCiMg"
    "dHdvIHJlbmRlcmVkIHBlciBtb2RlLgojCiMgTGlnaHQgc3BlbmRzIGl0cyBkZXJpdmF0"
    "aXZlIG9uIEJSQU5EX0RBUktfR09MRF9ERUVQLCBhbmQgdGhhdCBvbmUgaXMKIyBzdHJ1"
    "Y3R1cmFsOiBnb2xkIGFzIHRleHQgb24gYW55IGxpZ2h0IHN1cmZhY2UgYmVsb3cgd2hp"
    "dGUgbmVlZHMgYSBkYXJrZXIKIyB2YWx1ZSB0aGFuIGdvbGQgYXMgYSBmaWxsIHVuZGVy"
    "IGJsYWNrIHRleHQsIGFuZCB0aG9zZSB0d28gbHVtaW5hbmNlIGJhbmRzCiMgZG8gbm90"
    "IG92ZXJsYXAuCiMKIyBEYXJrIHNwZW5kcyBpdHMgZGVyaXZhdGl2ZSBvbiBob3Zlciwg"
    "d2hpY2ggbGlmdHMgYXdheSBmcm9tIHRoZSBkYXJrCiMgZ3JvdW5kLiBQcmVzc2VkIHJl"
    "dHVybnMgdG8gdGhlIGFjY2VudCBpbiBib3RoIG1vZGVzIC0tIHRoYXQgaXMgd2hhdCBo"
    "b2xkcwojIHRoZSBjb3VudCBhdCB0d28uCiMKIyBXaHkgY291bnQgYXQgYWxsLCB3aGVu"
    "IGV2ZXJ5IHBhaXJpbmcgYWxyZWFkeSBnZXRzIGEgY29udHJhc3QgY2hlY2s6IGFuCiMg"
    "ZXh0cmEgZ29sZCBpcyB1c3VhbGx5IHBlcmZlY3RseSBsZWdpYmxlLiBybnYtY29sb3It"
    "cGlja2VyIGNhcnJpZWQKIyAjYzRhNDU4IGZvciBtb250aHMsIGEgdGludCBvZiBhIGdv"
    "bGQgdGhhdCBoYWQgYWxyZWFkeSBiZWVuIHJldGlyZWQsCiMgcmVuZGVyaW5nIG9uIG9u"
    "ZSBrZXkgd2l0aCBub3RoaW5nIGFueXdoZXJlIHRvIG5vdGljZS4gQ29udHJhc3QgdGVz"
    "dHMKIyBjYW5ub3Qgc2VlIHRoYXQuIENvdW50aW5nIGNhbi4KCkdPTERfQ09OU1RBTlRT"
    "ID0gKCdCUkFORF9HT0xEJywgJ0JSQU5EX0RBUktfR09MRCcsICdCUkFORF9EQVJLX0dP"
    "TERfREVFUCcsCiAgICAgICAgICAgICAgICAgICdHT0xEX0hPVkVSJywgJ0dPTERfUFJF"
    "U1NFRCcsICdCUkFORF9EQVJLX0dPTERfUFJFU1NFRCcpCgoKZGVmIF90aGVtZV9kaWN0"
    "cygpIC0+IGRpY3Rbc3RyLCBkaWN0XToKICAgICIiIlRoZSB0d28gdGhlbWUgZGljdHMs"
    "IHJlc29sdmVkIGZyb20gc291cmNlLgoKICAgIFJlYWQgdGhyb3VnaCB0aGUgQVNUIHJh"
    "dGhlciB0aGFuIGltcG9ydGVkIGJlY2F1c2UgdGhlIGRpY3RzIGFyZSBidWlsdAogICAg"
    "aW5saW5lIGluIGRpYWxvZ19zdHlsZXMgYW5kIHRoZXJlIGlzIG5vIGFjY2Vzc29yIHRo"
    "YXQgaGFuZHMgdGhlbSBvdmVyLgogICAgIiIiCiAgICBzcmMgPSBTVFlMRVMucmVhZF90"
    "ZXh0KGVuY29kaW5nPSd1dGYtOCcpCiAgICBvdXQgPSB7fQogICAgZm9yIG5vZGUgaW4g"
    "YXN0LndhbGsoYXN0LnBhcnNlKHNyYykpOgogICAgICAgIGlmIG5vdCBpc2luc3RhbmNl"
    "KG5vZGUsIGFzdC5EaWN0KSBvciBsZW4obm9kZS5rZXlzKSA8PSAzMDoKICAgICAgICAg"
    "ICAgY29udGludWUKICAgICAgICBkID0ge30KICAgICAgICBmb3IgaywgdiBpbiB6aXAo"
    "bm9kZS5rZXlzLCBub2RlLnZhbHVlcyk6CiAgICAgICAgICAgIGlmIG5vdCBpc2luc3Rh"
    "bmNlKGssIGFzdC5Db25zdGFudCk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAg"
    "ICAgICAgICBpZiBpc2luc3RhbmNlKHYsIGFzdC5Db25zdGFudCk6CiAgICAgICAgICAg"
    "ICAgICBkW2sudmFsdWVdID0gdi52YWx1ZQogICAgICAgICAgICBlbGlmIGlzaW5zdGFu"
    "Y2UodiwgYXN0Lk5hbWUpOgogICAgICAgICAgICAgICAgZFtrLnZhbHVlXSA9IGdldGF0"
    "dHIoY29sb3JzLCB2LmlkLCBOb25lKQogICAgICAgIG5hbWUgPSAoJ2RhcmsnIGlmIHN0"
    "cihkLmdldCgnYWNjZW50JywgJycpKS5sb3dlcigpCiAgICAgICAgICAgICAgICA9PSBj"
    "b2xvcnMuQlJBTkRfR09MRC5sb3dlcigpIGVsc2UgJ2xpZ2h0JykKICAgICAgICBvdXRb"
    "bmFtZV0gPSBkCiAgICByZXR1cm4gb3V0CgoKZGVmIHRlc3RfYm90aF90aGVtZV9kaWN0"
    "c193ZXJlX2ZvdW5kKCk6CiAgICAiIiJHdWFyZCB0aGUgZ3VhcmQuIElmIHRoZSBBU1Qg"
    "d2FsayBzdG9wcyBtYXRjaGluZywgZXZlcnkgY291bnQgYmVsb3cKICAgIHBhc3NlcyBi"
    "eSBtZWFzdXJpbmcgbm90aGluZy4iIiIKICAgIHRoZW1lcyA9IF90aGVtZV9kaWN0cygp"
    "CiAgICBhc3NlcnQgc2V0KHRoZW1lcykgPT0geydkYXJrJywgJ2xpZ2h0J30sICgKICAg"
    "ICAgICBmJ2V4cGVjdGVkIGEgZGFyayBhbmQgYSBsaWdodCB0aGVtZSBkaWN0LCBmb3Vu"
    "ZCB7c29ydGVkKHRoZW1lcyl9JykKICAgIGZvciBuYW1lLCBkIGluIHRoZW1lcy5pdGVt"
    "cygpOgogICAgICAgIGFzc2VydCBsZW4oZCkgPiAzMCwgZid7bmFtZX0gdGhlbWUgcmVz"
    "b2x2ZWQgb25seSB7bGVuKGQpfSBrZXlzJwoKCkBweXRlc3QubWFyay5wYXJhbWV0cml6"
    "ZSgnbW9kZScsIFsnZGFyaycsICdsaWdodCddKQpkZWYgdGVzdF90d29fZ29sZHNfcGVy"
    "X21vZGUobW9kZSk6CiAgICAiIiJUaGUgcnVsZSwgbWFkZSBtYWNoaW5lLWNoZWNrYWJs"
    "ZS4iIiIKICAgIGdvbGRzID0ge2dldGF0dHIoY29sb3JzLCBuKS5sb3dlcigpIGZvciBu"
    "IGluIEdPTERfQ09OU1RBTlRTfQogICAgZCA9IF90aGVtZV9kaWN0cygpW21vZGVdCiAg"
    "ICB1c2VkID0ge30KICAgIGZvciBrZXksIHZhbHVlIGluIGQuaXRlbXMoKToKICAgICAg"
    "ICBpZiBpc2luc3RhbmNlKHZhbHVlLCBzdHIpIGFuZCB2YWx1ZS5sb3dlcigpIGluIGdv"
    "bGRzOgogICAgICAgICAgICB1c2VkLnNldGRlZmF1bHQodmFsdWUubG93ZXIoKSwgW10p"
    "LmFwcGVuZChrZXkpCiAgICBhc3NlcnQgbGVuKHVzZWQpIDw9IDIsICdcbiAgJy5qb2lu"
    "KAogICAgICAgIFtmJ3ttb2RlfSB0aGVtZSBob2xkcyB7bGVuKHVzZWQpfSBkaXN0aW5j"
    "dCBnb2xkczsgdGhlIGJyYW5kIGFsbG93cyAnCiAgICAgICAgIGYndHdvIC0tIHRoZSBy"
    "ZWdpc3RlcmVkIG9uZSBhbmQgb25lIGRlcml2ZWQgZnJvbSBpdDonXQogICAgICAgICsg"
    "W2Yne3Z9ICAoe2xlbihrcyl9IGtleXMpICB7IiwgIi5qb2luKHNvcnRlZChrcylbOjVd"
    "KX0nCiAgICAgICAgICAgZm9yIHYsIGtzIGluIHNvcnRlZCh1c2VkLml0ZW1zKCkpXSkK"
    "CgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoJ21vZGUsYmFzZScsIFsoJ2RhcmsnLCAn"
    "QlJBTkRfR09MRCcpLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAoJ2xpZ2h0JywgJ0JSQU5EX0RBUktfR09MRCcpXSkKZGVmIHRlc3RfdGhlX3JlZ2lz"
    "dGVyZWRfZ29sZF9pc19vbmVfb2ZfdGhlX3R3byhtb2RlLCBiYXNlKToKICAgICIiIlR3"
    "byBnb2xkcyBuZWl0aGVyIG9mIHdoaWNoIGlzIHJlZ2lzdGVyZWQgd291bGQgc2F0aXNm"
    "eSBhIGJhcmUgY291bnQKICAgIHdoaWxlIGJlaW5nIGVudGlyZWx5IG9mZi1icmFuZC4i"
    "IiIKICAgIGQgPSBfdGhlbWVfZGljdHMoKVttb2RlXQogICAgd2FudCA9IGdldGF0dHIo"
    "Y29sb3JzLCBiYXNlKS5sb3dlcigpCiAgICBwcmVzZW50ID0ge3YubG93ZXIoKSBmb3Ig"
    "diBpbiBkLnZhbHVlcygpCiAgICAgICAgICAgICAgIGlmIGlzaW5zdGFuY2Uodiwgc3Ry"
    "KSBhbmQgdi5sb3dlcigpID09IHdhbnR9CiAgICBhc3NlcnQgcHJlc2VudCwgKGYne21v"
    "ZGV9IHRoZW1lIG5ldmVyIHVzZXMge2Jhc2V9ICh7d2FudH0pLCB0aGUgJwogICAgICAg"
    "ICAgICAgICAgICAgICBmJ3JlZ2lzdGVyZWQgZ29sZCBmb3IgdGhpcyBtb2RlJykKCgpk"
    "ZWYgdGVzdF9wcmVzc2VkX3JldHVybnNfdG9fdGhlX2FjY2VudF9pbl9ib3RoX21vZGVz"
    "KCk6CiAgICAiIiJXaGF0IGtlZXBzIHRoZSBjb3VudCBhdCB0d28uIEJlZm9yZSB0aGlz"
    "IHBhc3MgR09MRF9QUkVTU0VEIHdhcwogICAgI2JiYTU3YyAtLSBhIHRoaXJkIGdvbGQg"
    "d2hvc2Ugb25seSBqb2Igd2FzIGEgMnB4IHRhYiB1bmRlcmxpbmUuIiIiCiAgICBhc3Nl"
    "cnQgY29sb3JzLkdPTERfUFJFU1NFRCA9PSBjb2xvcnMuQlJBTkRfR09MRAogICAgYXNz"
    "ZXJ0IGNvbG9ycy5CUkFORF9EQVJLX0dPTERfUFJFU1NFRCA9PSBjb2xvcnMuQlJBTkRf"
    "REFSS19HT0xECgoKZGVmIHRlc3Rfbm9fdGhlbWVfa2V5X2lzX2RlZmluZWRfdHdpY2Uo"
    "KToKICAgICIiIkEgZHVwbGljYXRlIGtleSBpcyBzaWxlbnRseSB3b24gYnkgdGhlIGxh"
    "c3Qgb25lLgoKICAgIEJvdGggdGhlbWUgZGljdHMgbGlzdGVkICdhY2NlbnRfaW5rJyB0"
    "d2ljZS4gU2FtZSB2YWx1ZSBlYWNoIHRpbWUsIHNvIGl0CiAgICBjaGFuZ2VkIG5vdGhp"
    "bmcgLS0gYnV0IHRoZSBkYXkgdGhlIHR3byBsaW5lcyBkaWZmZXIsIHRoZSBmaXJzdCBp"
    "cyBkZWFkCiAgICBjb2RlIHRoYXQgcmVhZHMgYXMgbGl2ZS4KICAgICIiIgogICAgc3Jj"
    "ID0gU1RZTEVTLnJlYWRfdGV4dChlbmNvZGluZz0ndXRmLTgnKQogICAgZHVwZXMgPSBb"
    "XQogICAgZm9yIG5vZGUgaW4gYXN0LndhbGsoYXN0LnBhcnNlKHNyYykpOgogICAgICAg"
    "IGlmIG5vdCBpc2luc3RhbmNlKG5vZGUsIGFzdC5EaWN0KToKICAgICAgICAgICAgY29u"
    "dGludWUKICAgICAgICBrZXlzID0gW2sudmFsdWUgZm9yIGsgaW4gbm9kZS5rZXlzIGlm"
    "IGlzaW5zdGFuY2UoaywgYXN0LkNvbnN0YW50KV0KICAgICAgICBmb3IgayBpbiBzb3J0"
    "ZWQoe2sgZm9yIGsgaW4ga2V5cyBpZiBrZXlzLmNvdW50KGspID4gMX0pOgogICAgICAg"
    "ICAgICBkdXBlcy5hcHBlbmQoZid1dGlscy9kaWFsb2dfc3R5bGVzLnB5Ontub2RlLmxp"
    "bmVub306ICcKICAgICAgICAgICAgICAgICAgICAgICAgIGYne2shcn0gZGVmaW5lZCB7"
    "a2V5cy5jb3VudChrKX0gdGltZXMnKQogICAgYXNzZXJ0IG5vdCBkdXBlcywgJ1xuICAn"
    "LmpvaW4oZHVwZXMpCg=="
)

QT_APT_PACKAGES = (
    "libegl1 libgl1 libglib2.0-0 libdbus-1-3 libfontconfig1 "
    "libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 "
    "libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 "
    "libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0"
)

FAIL, OK, WARN, OFF = "\033[31m", "\033[32m", "\033[33m", "\033[0m"


def say(msg: str, colour: str = "") -> None:
    print(f"{colour}{msg}{OFF}" if colour else msg)


def die(msg: str) -> None:
    say(f"ABORT: {msg}", FAIL)
    sys.exit(1)


def read_any(path: Path) -> tuple[str, str]:
    """Read a file that may carry a BOM or non-UTF-8 bytes, losslessly."""
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        return raw.decode("utf-8-sig" if bom else "utf-8"), ("bom" if bom else "plain")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="surrogateescape"), "surrogate"


def write_any(path: Path, text: str, mode: str) -> None:
    if mode == "bom":
        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    elif mode == "surrogate":
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as fh:
            fh.write(text)
    else:
        path.write_text(text, encoding="utf-8")


def _lum(h: str) -> float:
    h = h.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    l1, l2 = sorted([_lum(a), _lum(b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# ══════════════════════════════════════════════════════════════════════════
# PREFLIGHT
# ══════════════════════════════════════════════════════════════════════════

def diagnose(err: str) -> str | None:
    m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", err)
    if m:
        return (f"the Python package {m.group(1)!r} is not installed.\n\n"
                f"       Fix:\n"
                f"         pip install -r requirements.txt -r requirements-dev.txt")
    m = re.search(r"ImportError: (lib[\w.+-]*\.so[.\d]*): cannot open shared "
                  r"object file", err)
    if m:
        return (f"PyQt6 cannot load: the system library {m.group(1)} is "
                f"missing.\n"
                f"       The Python package is installed; the C libraries it "
                f"links against are not.\n"
                f"       QT_QPA_PLATFORM=offscreen does not help -- the object "
                f"fails to open first.\n\n"
                f"       Fix, in one command:\n"
                f"         python {SELF.name} --install-deps")
    return None


def install_system_deps() -> None:
    """Install the Qt system libraries, on request only."""
    if os.name != "posix":
        die("--install-deps is for Debian/Ubuntu.")
    for cmd in (["sudo", "apt-get", "update"],
                ["sudo", "apt-get", "install", "-y", "--no-install-recommends",
                 *QT_APT_PACKAGES.split()]):
        say(f"    $ {' '.join(cmd[:5])}{' ...' if len(cmd) > 5 else ''}")
        if subprocess.run(cmd).returncode != 0:
            die(f"'{' '.join(cmd[:3])}' failed. As root, by hand:\n"
                f"         apt-get install -y --no-install-recommends "
                f"{QT_APT_PACKAGES}")
    say("system Qt libraries installed", OK)


def check_dependencies() -> None:
    """Probe for real, in a subprocess, doing what the tests will do.

    importlib.util.find_spec proves a module is FINDABLE, not importable.
    """
    probe = ("import pytest, syrupy\n"
             "import os; os.environ.setdefault('QT_QPA_PLATFORM','offscreen')\n"
             "from PyQt6.QtWidgets import QApplication\n")
    r = subprocess.run([sys.executable, "-c", probe], cwd=REPO,
                       capture_output=True, text=True,
                       env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    if r.returncode != 0:
        hint = diagnose(r.stderr) or (
            "the test imports fail here:\n\n"
            + "\n".join(f"       {ln}"
                        for ln in r.stderr.strip().splitlines()[-6:]))
        die(f"{hint}\n\n       Nothing has been changed.")
    say("preflight: dependencies present", OK)


def preflight() -> None:
    check_dependencies()
    for path in (COLORS, STYLES, GUARD):
        if not path.exists():
            die(f"{path.relative_to(REPO)} not found -- run this from the "
                f"repository root.")
    src, _ = read_any(COLORS)
    if "GOLD_PRESSED: Final[str] = BRAND_GOLD" in src:
        die("GOLD_PRESSED already aliases BRAND_GOLD. This pass has been "
            "applied. Nothing changed.")
    if "GOLD_PRESSED: Final[str] = lighten(BRAND_GOLD, -23)" not in src:
        die("GOLD_PRESSED is not in the expected form in utils/colors.py. "
            "This repository is not at the state the script was proven "
            "against. Nothing changed.")
    say("preflight: base state confirmed", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 1 -- the third gold
# ══════════════════════════════════════════════════════════════════════════

OLD_PRESSED = (
    "#: dark-mode pressed. Same derivation, same reasoning (replaces #b7a480,\n"
    "#: RGB distance 3.3, hue drift 39.3 -> 39.0). Dark mode has room for a distinct\n"
    "#: pressed state; light mode does not, which is why BRAND_DARK_GOLD_PRESSED is\n"
    "#: the accent itself and this is not.\n"
    "GOLD_PRESSED: Final[str] = lighten(BRAND_GOLD, -23)"
)

NEW_PRESSED = (
    "#: dark-mode pressed. It IS the accent, mirroring light mode.\n"
    "#:\n"
    "#: The brand registers two golds and derives the rest when needed. Each mode\n"
    "#: gets the registered gold and ONE derivative -- light spends its on\n"
    "#: BRAND_DARK_GOLD_DEEP, dark spends its on GOLD_HOVER -- and every other gold\n"
    "#: role reuses one of the two. Pressed returning to rest is what holds the\n"
    "#: count there, and tests/test_brand_mirror.py asserts the count.\n"
    "#:\n"
    "#: This replaced lighten(BRAND_GOLD, -23) = #bba57c, a third gold whose only\n"
    "#: consumer was a 2px tab underline. On the dark hover ground #3a3a3a that\n"
    "#: underline moves 4.7589 -> 6.1503, both above the 3.0 component floor, so\n"
    "#: nothing was failing -- which is the point. An extra gold is usually\n"
    "#: perfectly legible, so only counting finds it.\n"
    "#:\n"
    "#: The interaction still reads: rest at the accent, hover lifts away from the\n"
    "#: dark ground, pressed drops back to rest.\n"
    "GOLD_PRESSED: Final[str] = BRAND_GOLD"
)


def step_pressed() -> None:
    src, mode = read_any(COLORS)
    if OLD_PRESSED not in src:
        die("the GOLD_PRESSED block in utils/colors.py is not in the "
            "expected form. Nothing changed.")
    write_any(COLORS, src.replace(OLD_PRESSED, NEW_PRESSED, 1), mode)
    say("step 1: GOLD_PRESSED now aliases BRAND_GOLD -- dark drops to 2 golds",
        OK)


def step_stale_comment() -> None:
    """The paragraph above the variants says dark mode is 'still minting'.

    It stopped being true when GOLD_HOVER and GOLD_PRESSED were derived,
    and it is fully untrue now. A comment that describes a state the code
    left behind is worse than no comment: it is read as current.
    """
    src, mode = read_any(COLORS)
    stale = ("# The light-mode equivalents ARE derived (BRAND_DARK_GOLD_DEEP). "
             "Dark\n# mode is the half still minting, and a future pass should "
             "close it --\n# which would change these values, so it is not this "
             "pass.")
    if stale not in src:
        say("step 2: the 'still minting' note is not in the expected form, "
            "left alone", WARN)
        return
    fresh = ("# That future pass is this one. Dark mode now runs on two golds:\n"
             "# BRAND_GOLD and GOLD_HOVER derived from it. GOLD_PRESSED returned\n"
             "# to the accent, which is where the third value went.")
    write_any(COLORS, src.replace(stale, fresh, 1), mode)
    say("step 2: the 'dark mode is still minting' note updated -- it "
        "describes a state the code has left", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 3 -- the duplicate keys
# ══════════════════════════════════════════════════════════════════════════

def step_duplicate_keys() -> None:
    """Remove the second 'accent_ink' from each theme dict.

    Found by parsing, and the count is asserted: a blind replace of a line
    that appears twice removes the wrong one as happily as the right one.
    """
    src, mode = read_any(STYLES)
    dupes = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Dict):
            continue
        keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
        for key in {k for k in keys if keys.count(k) > 1}:
            dupes.append((node.lineno, key, keys.count(key)))
    if not dupes:
        say("step 3: no duplicate theme keys found", WARN)
        return
    if {k for _, k, _ in dupes} != {"accent_ink"}:
        die(f"expected only 'accent_ink' duplicated and found "
            f"{sorted({k for _, k, _ in dupes})}. Nothing further changed.")

    lines = src.splitlines(keepends=True)
    # Collect the second occurrence of each duplicated key, by line, so the
    # first (and its comment) survives.
    doomed = set()
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Dict):
            continue
        seen = {}
        for k in node.keys:
            if not isinstance(k, ast.Constant):
                continue
            if k.value in seen:
                doomed.add(k.lineno)
            seen[k.value] = k.lineno
    if len(doomed) != len(dupes):
        die(f"expected {len(dupes)} duplicate lines and located "
            f"{len(doomed)}. Nothing further changed.")
    out = [ln for i, ln in enumerate(lines, 1) if i not in doomed]
    new = "".join(out)
    ast.parse(new)          # never write a file that will not parse
    write_any(STYLES, new, mode)
    say(f"step 3: removed {len(doomed)} duplicate 'accent_ink' key(s) "
        f"(lines {sorted(doomed)})", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 4 -- the guard
# ══════════════════════════════════════════════════════════════════════════

def step_guard() -> None:
    src, mode = read_any(GUARD)
    if GUARD_MARKER in src:
        say("step 4: the count guard is already present", WARN)
        return
    block = base64.b64decode(GUARD_BLOCK_B64).decode("utf-8")
    new = src.rstrip("\n") + "\n" + block
    ast.parse(new)
    write_any(GUARD, new, mode)
    say(f"step 4: count guard appended to tests/test_brand_mirror.py "
        f"({len(block.splitlines())} lines)", OK)


# ══════════════════════════════════════════════════════════════════════════
# STEP 5 -- snapshots
# ══════════════════════════════════════════════════════════════════════════

def step_snapshots() -> None:
    """Regenerate the syrupy snapshot, which carries the underline colour."""
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_snapshots.py",
                        "--snapshot-update", "-q"],
                       cwd=REPO, env=env, capture_output=True, text=True)
    snap = REPO / "tests" / "__snapshots__" / "test_snapshots.ambr"
    if not snap.exists():
        die("tests/__snapshots__/test_snapshots.ambr vanished. "
            f"{r.stdout[-1500:]}")
    body = snap.read_text(encoding="utf-8", errors="ignore").lower()
    if RETIRED_GOLD in body:
        hint = diagnose(r.stderr or r.stdout)
        die((hint + "\n\n       " if hint else "")
            + f"the snapshot still carries {RETIRED_GOLD} after "
              f"regeneration.\n{r.stdout[-1500:]}")
    say("step 5: snapshot regenerated", OK)


# ══════════════════════════════════════════════════════════════════════════
# VERIFY
# ══════════════════════════════════════════════════════════════════════════

def tracked(*suffixes: str) -> list[Path]:
    r = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        die("git ls-files failed -- run this inside the repository.")
    out = []
    for name in r.stdout.split("\0"):
        if not name:
            continue
        p = (REPO / name).resolve()
        if p == SELF or not p.exists():
            continue
        if suffixes and p.suffix not in suffixes:
            continue
        if p.suffix == ".py":
            try:
                if TOOL_MARKER in p.read_text(encoding="utf-8", errors="ignore"):
                    continue
            except OSError:
                pass
        out.append(p)
    return sorted(out)


MENTION = re.compile(
    r"\b(was|were|previously|formerly|used to|replaced|retired|legacy|"
    r"deprecated|old value|superseded|orphaned|hand-written)\b", re.I)


def verify() -> bool:
    ok = True
    for m in [k for k in list(sys.modules) if k.split(".")[0] in
              ("utils", "ui", "core", "cli")]:
        del sys.modules[m]
    sys.path.insert(0, str(REPO))
    from utils import colors as C  # noqa: E402

    if C.GOLD_PRESSED != C.BRAND_GOLD:
        ok = False
        say(f"verify: GOLD_PRESSED is {C.GOLD_PRESSED}, expected the accent "
            f"{C.BRAND_GOLD}", FAIL)
    if C.GOLD_HOVER != C.lighten(C.BRAND_GOLD, 13):
        ok = False
        say("verify: GOLD_HOVER no longer tracks BRAND_GOLD", FAIL)

    # GOLD_PRESSED must be an alias, not a literal -- an alias tracks its
    # source, a written-down copy does not.
    tree = ast.parse(read_any(COLORS)[0])
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            tgt, val = node.target.id, node.value
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            tgt, val = node.targets[0].id, node.value
        if tgt == "GOLD_PRESSED" and not isinstance(val, ast.Name):
            ok = False
            say("verify: GOLD_PRESSED should alias BRAND_GOLD by name", FAIL)

    # the retired third gold must be gone from everything but a guard file
    guards, stale = 0, []
    for path in tracked(".py", ".md", ".ambr", ".json"):
        text = read_any(path)[0]
        if GUARD_MARKER in text:
            guards += 1
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if MENTION.search(line):
                continue
            if RETIRED_GOLD in line.lower():
                stale.append(f"{path.relative_to(REPO)}:{i}: {line.strip()[:60]}")
    if stale:
        ok = False
        say(f"verify: the retired third gold {RETIRED_GOLD} is still here:", FAIL)
        for s in stale:
            say(f"        {s}", FAIL)
    if guards != 1:
        ok = False
        say(f"verify: expected exactly one guard file carrying the marker, "
            f"found {guards}", FAIL)

    # the underline still clears its floor
    r = contrast(C.GOLD_PRESSED, "#3a3a3a")
    if r < 3.0:
        ok = False
        say(f"verify: the dark tab underline measures {r:.4f} against the "
            f"3.0 component floor", FAIL)
    else:
        say(f"verify: dark tab underline {C.GOLD_PRESSED} on #3a3a3a = "
            f"{r:.4f}")

    say("verify: PASS" if ok else "verify: FAIL", OK if ok else FAIL)
    return ok


PYTEST_EXIT = {
    0: ("all tests passed", OK),
    1: ("tests FAILED -- see above", FAIL),
    2: ("the run was interrupted", WARN),
    3: ("pytest internal error", WARN),
    4: ("pytest usage error", WARN),
    5: ("NO TESTS RAN. That is not a pass.", FAIL),
}


def classify(code: int) -> str:
    return "killed" if code < 0 else ("pass" if code == 0 else "fail")


def _run(args: list[str], label: str) -> str:
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    say(f"running {label} ...")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", *args],
                       cwd=REPO, env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    keep = [ln for ln in out if ln.startswith(("FAILED", "ERROR"))
            or " failed" in ln or " passed" in ln]
    for line in (keep or out)[-12:]:
        say(f"    {line}")
    if r.returncode < 0:
        sig = -r.returncode
        name = {9: "SIGKILL -- out of memory",
                15: "SIGTERM -- something asked it to stop; on a codespace "
                    "driven from a browser\n         this is usually the "
                    "session being reclaimed, not the tests"}.get(
                        sig, f"signal {sig}")
        say(f"\n    the test process was KILLED by {name}", WARN)
        say("    Not a test result. CI runs the full suite on every push.",
            WARN)
        return "killed"
    msg, colour = PYTEST_EXIT.get(r.returncode,
                                  (f"pytest exited {r.returncode}", WARN))
    say(f"    {msg}", colour)
    return classify(r.returncode)


def run_guard_tests() -> str:
    return _run(["tests/test_brand_mirror.py", "tests/test_contrast_pairs.py"],
                "the guard suites")


def run_suite() -> str:
    return _run(["tests/", "--benchmark-disable"], "the full test suite")


def remove_helpers(extra: list[str]) -> None:
    doomed = [p for p in tracked(".py", ".sh", ".md")
              if TOOL_MARKER in read_any(p)[0]]
    if SELF.exists() and SELF not in doomed:
        doomed.append(SELF)
    for name in extra:
        p = (REPO / name).resolve()
        if not p.exists():
            say(f"    {name}: not here, nothing to remove", WARN)
        elif p not in doomed:
            doomed.append(p)
    for p in sorted(set(doomed)):
        try:
            p.unlink()
            say(f"    removed {p.relative_to(REPO)}", OK)
        except OSError as exc:
            say(f"    could NOT remove {p.relative_to(REPO)}: {exc}", FAIL)
    say("\n    Working tree is ready. One commit takes everything:", OK)
    say("      git add -A")
    say("      git commit -m 'Two golds per mode: pressed returns to the "
        "accent; guard the count'")
    say("      git push")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Two golds per mode for rnv-text-transformer.")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--install-deps", action="store_true",
                    help="apt-get the Qt system libraries, then continue")
    ap.add_argument("--finish", nargs="*", metavar="FILE",
                    help="verify, run the guard suites, then delete this tool "
                         "and any extra FILEs. Deletion only if all passed.")
    ap.add_argument("--skip-tests", action="store_true",
                    help="skip the full suite; the guard suites always run")
    args = ap.parse_args()

    if args.install_deps:
        install_system_deps()

    # Apply unless asked only to check. Whether --finish was passed is a
    # question about CLEANUP, not about whether to apply -- the first draft
    # conflated them, so `--finish` on a base clone verified an unchanged
    # repository, failed, and correctly refused to delete anything. One
    # command should apply, verify and tidy up, because that is one commit.
    applied = "GOLD_PRESSED: Final[str] = BRAND_GOLD" in read_any(COLORS)[0]
    if args.verify_only:
        pass
    elif applied:
        say("already applied -- skipping to verification", WARN)
    else:
        preflight()
        step_pressed()
        step_stale_comment()
        step_duplicate_keys()
        step_guard()
        step_snapshots()

    ok = verify()
    if run_guard_tests() != "pass":
        ok = False

    if args.finish is not None:
        if not args.skip_tests and run_suite() == "fail":
            ok = False
        if ok:
            say("\nremoving transfer helpers ...")
            remove_helpers(args.finish)
        else:
            say("\nNOT removing anything -- the checks did not pass. The "
                "tools stay so you can find out why.", FAIL)
    elif not args.skip_tests:
        if run_suite() == "fail":
            ok = False

    say("\nDONE -- all checks passed" if ok
        else "\nDONE -- with failures above", OK if ok else FAIL)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
