import re

# Every GDS prints a codeshare's operator on its own line under the segment.
_OPERATED_BY = re.compile(r"^\s*OPERATED BY\s*/?\s*(?P<operator>\S.*?)\s*$")

# Glyphs some terminals append to a response (Sabre ends one with `«`).
_TERMINAL_MARKERS = str.maketrans("", "", "«")


def normalize_pnr_text(text: str) -> str:
    text = text.translate(_TERMINAL_MARKERS)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(8).split("\n")
    return "\n".join(line.rstrip().upper() for line in lines).strip("\n")


def operating_carrier(line: str) -> str | None:
    """The operator named by an `OPERATED BY …` line, if this is one."""
    match = _OPERATED_BY.match(line)
    return match["operator"] if match else None
