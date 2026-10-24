from scripts.build_airlines import OVERRIDES, build


def _row(name: str, iata: str, active: str = "Y") -> list[str]:
    return ["1", name, r"\N", iata, "ICA", "CALL", "Country", active]


def test_keeps_active_airlines_with_valid_iata_codes() -> None:
    rows = [
        _row("Tarom", "RO"),
        _row("Defunct Air", "DF", active="N"),
        _row("No Code", ""),
        _row("Bad Code", "R-"),
        ["truncated", "row"],
    ]
    assert build(rows) == {"RO": "Tarom", **OVERRIDES}


def test_drops_ambiguous_codes() -> None:
    rows = [_row("First Air", "Q1"), _row("Second Air", "Q1")]
    assert "Q1" not in build(rows)


def test_overrides_resolve_ambiguous_codes() -> None:
    rows = [_row("Vueling Airlines", "VY"), _row("Formosa Airlines", "VY")]
    assert build(rows)["VY"] == "Vueling Airlines"


def test_output_is_sorted_by_code() -> None:
    codes = list(build([_row("Zed Air", "ZZ"), _row("Alpha Air", "AA")]))
    assert codes == sorted(codes)
