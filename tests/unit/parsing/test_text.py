from pnr_convertor.parsing.text import normalize_pnr_text


def test_normalizes_line_endings_case_and_trailing_whitespace() -> None:
    raw = "\r\nrp/abc   \r\n  1.doe/jane\t\r\n\r\n"
    assert normalize_pnr_text(raw) == "RP/ABC\n  1.DOE/JANE"
