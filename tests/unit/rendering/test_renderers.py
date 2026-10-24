from __future__ import annotations

from pnr_convertor.application.enrich_itinerary import ItineraryEnricher
from pnr_convertor.domain.itinerary import Itinerary
from pnr_convertor.domain.models import Contact, ContactKind, GdsFormat, ParsedPnr, Passenger
from pnr_convertor.rendering import HtmlItineraryRenderer, TextItineraryRenderer
from tests.factories import InMemoryAirlineRepository, InMemoryAirportRepository, make_segment

ENRICHER = ItineraryEnricher(InMemoryAirportRepository(), InMemoryAirlineRepository())


def _itinerary(contact: str) -> Itinerary:
    return ENRICHER.enrich(
        ParsedPnr(
            GdsFormat.AMADEUS,
            None,
            (Passenger(1, "DOE", "JANE", "MRS"),),
            (make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", status="HX"),),
            contacts=(Contact(ContactKind.PHONE, contact),),
        )
    )


def test_html_escapes_pnr_text() -> None:
    html = HtmlItineraryRenderer().render(_itinerary("<script>alert(1)</script>"))

    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_text_keeps_pnr_text_verbatim() -> None:
    text = TextItineraryRenderer().render(_itinerary("BUH 021 <555> & CO"))
    assert "Phone: BUH 021 <555> & CO" in text


def test_cancelled_only_itinerary_without_locator() -> None:
    itinerary = _itinerary("BUH 021 555 0100")
    text = TextItineraryRenderer().render(itinerary)
    html = HtmlItineraryRenderer().render(itinerary)

    assert "Booking reference" not in text
    assert "TRIP 1" not in text
    assert "CANCELLED FLIGHTS" in text
    assert '<span class="status cancelled">Cancelled</span>' in html


def test_media_types_and_formats() -> None:
    text, html = TextItineraryRenderer(), HtmlItineraryRenderer()
    assert (text.format.value, text.media_type) == ("text", "text/plain")
    assert (html.format.value, html.media_type) == ("html", "text/html")
