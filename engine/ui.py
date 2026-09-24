"""Terminal colouring for the CLI.

ANSI escapes only — no dependency, and everything degrades to plain text when
stdout is not a terminal (a redirected log stays readable) or NO_COLOR is set.
"""
from __future__ import annotations

import os
import re
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

# Old Windows consoles need VT processing switched on; one no-op os.system call
# does it. Windows Terminal already has it and does not care.
if os.name == "nt":
    os.system("")

ENABLED = bool(getattr(sys.stdout, "isatty", lambda: False)()) and not os.environ.get("NO_COLOR")

# One colour per pipeline stage, so a long run reads as bands instead of a wall.
TAGS = {
    "tema": MAGENTA,
    "investigación": BLUE,
    "bibliografía": BLUE,
    "esquema": CYAN,
    "borrador": CYAN,
    "revisión": YELLOW,
    "detector": YELLOW,
    "aprobación": GREEN,
    "publicación": GREEN,
    "continuo": MAGENTA,
    "retomar": DIM,
    "error": RED,
}

_TAG = re.compile(r"^(\s*)\[([^\]]+)\]")


def c(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes, or return it untouched when colour is off."""
    return f"{''.join(codes)}{text}{RESET}" if ENABLED else text


def rule(title: str) -> str:
    return c(f"═══ {title} ═══", BOLD, CYAN)


def _line(line: str) -> str:
    m = _TAG.match(line)
    if m:
        colour = TAGS.get(m.group(2).split()[0].lower(), CYAN)
        return f"{m.group(1)}{c('[' + m.group(2) + ']', BOLD, colour)}{line[m.end():]}"
    stripped = line.strip()
    if stripped and not stripped.strip("─═-="):  # box-drawing separators
        return c(line, CYAN)
    if stripped.startswith(("·", "-")):
        return c(line, DIM)
    return line


_LAST_TAG: str | None = None


def log(msg: str = "") -> None:
    """print() with the [etapa] prefix, separators and bullets coloured.

    A blank line separates each change of stage tag, so a long run reads as
    blocks instead of a wall of text.
    """
    global _LAST_TAG
    m = _TAG.match(str(msg))
    if m:
        tag = m.group(2).split()[0].lower()
        if _LAST_TAG is not None and tag != _LAST_TAG:
            print()
        _LAST_TAG = tag
    if not ENABLED:
        print(msg)
        return
    print("\n".join(_line(l) for l in str(msg).split("\n")))


def demo() -> None:
    assert _line("hola") == "hola"
    if not ENABLED:  # nothing else is observable with colour off
        return
    assert _line("[tema] x") == c("[tema]", BOLD, MAGENTA) + " x"
    assert _line("  [detector] y").startswith("  ")
    assert _line("[loquesea] z").startswith(BOLD + CYAN)
    assert _line("  · nota").startswith(DIM)
    assert _line("─────").startswith(CYAN)
    log("[tema] «Un título»\n  · una nota\n─────\n[error] algo falló")


if __name__ == "__main__":
    demo()
