# Glyphs some terminals append to a response (Sabre ends one with `«`).
_TERMINAL_MARKERS = str.maketrans("", "", "«")


def normalize_pnr_text(text: str) -> str:
    text = text.translate(_TERMINAL_MARKERS)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(8).split("\n")
    return "\n".join(line.rstrip().upper() for line in lines).strip("\n")
