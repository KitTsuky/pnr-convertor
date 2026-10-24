def normalize_pnr_text(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(8).split("\n")
    return "\n".join(line.rstrip().upper() for line in lines).strip("\n")
