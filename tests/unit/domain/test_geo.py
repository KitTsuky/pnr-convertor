import pytest

from pnr_convertor.domain.geo import KM_PER_MILE, distance_km
from tests.factories import AIRPORTS


@pytest.mark.parametrize(
    ("origin", "destination", "expected_miles"),
    [
        # Sabre VI* shows 3452 for JFK-LHR; IATA ticketed point mileage is 3451.
        ("JFK", "LHR", 3451),
        ("OTP", "CDG", 1153),
    ],
)
def test_distance_matches_ticketed_point_mileage(
    origin: str, destination: str, expected_miles: int
) -> None:
    miles = distance_km(AIRPORTS[origin], AIRPORTS[destination]) / KM_PER_MILE
    assert round(miles) == expected_miles


def test_distance_is_symmetric() -> None:
    there = distance_km(AIRPORTS["OTP"], AIRPORTS["DXB"])
    back = distance_km(AIRPORTS["DXB"], AIRPORTS["OTP"])
    assert there == pytest.approx(back)
