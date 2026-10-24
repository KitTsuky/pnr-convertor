from pnr_convertor.parsing.text import normalize_pnr_text


def test_normalizes_line_endings_case_and_trailing_whitespace() -> None:
    raw = "\r\nrp/abc   \r\n  1.doe/jane\t\r\n\r\n"
    assert normalize_pnr_text(raw) == "RP/ABC\n  1.DOE/JANE"


def test_strips_terminal_end_markers() -> None:
    assert normalize_pnr_text("*IA«\n 1 AA 142V«") == "*IA\n 1 AA 142V"
