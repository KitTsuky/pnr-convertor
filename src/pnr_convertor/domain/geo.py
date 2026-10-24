from __future__ import annotations

from geographiclib.geodesic import Geodesic

from pnr_convertor.domain.reference import Airport

KM_PER_MILE = 1.609344


def distance_km(origin: Airport, destination: Airport) -> float:
    """Shortest distance on the WGS84 ellipsoid, the basis of IATA ticketed point mileage."""
    geodesic = Geodesic.WGS84.Inverse(
        origin.latitude, origin.longitude, destination.latitude, destination.longitude
    )
    return float(geodesic["s12"]) / 1000
