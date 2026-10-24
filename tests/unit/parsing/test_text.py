import pytest

from pnr_convertor.parsing.text import normalize_pnr_text, operating_carrier


def test_normalizes_line_endings_case_and_trailing_whitespace() -> None:
    raw = "\r\nrp/abc   \r\n  1.doe/jane\t\r\n\r\n"
    assert normalize_pnr_text(raw) == "RP/ABC\n  1.DOE/JANE"


def test_strips_terminal_end_markers() -> None:
    assert normalize_pnr_text("*IA«\n 1 AA 142V«") == "*IA\n 1 AA 142V"


@pytest.mark.parametrize(
    ("line", "operator"),
    [
        ("OPERATED BY BRITISH AIRWAYS", "BRITISH AIRWAYS"),
        ("         OPERATED BY BRUSSELS AIRLINES", "BRUSSELS AIRLINES"),
        ("OPERATED BY /SKYWEST DBA UNITED EXPRESS", "SKYWEST DBA UNITED EXPRESS"),
        ("OPERATED BY KLM CITYHOP", "KLM CITYHOP"),
        ("1.1DOE/JANE MRS", None),
        ("OPERATED BY", None),
    ],
)
def test_operating_carrier(line: str, operator: str | None) -> None:
    assert operating_carrier(line) == operator
