from __future__ import annotations

from functools import cache

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from pnr_convertor.application.ports import RenderFormat
from pnr_convertor.domain.itinerary import Itinerary
from pnr_convertor.rendering.view import build_view


@cache
def _environment() -> Environment:
    return Environment(
        loader=PackageLoader("pnr_convertor.rendering"),
        # PNR text is untrusted: every value in an HTML template is escaped.
        autoescape=select_autoescape(enabled_extensions=("html.j2",), default_for_string=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


class TextItineraryRenderer:
    def __init__(self) -> None:
        self._template = _environment().get_template("itinerary.txt.j2")

    @property
    def format(self) -> RenderFormat:
        return RenderFormat.TEXT

    @property
    def media_type(self) -> str:
        return "text/plain"

    def render(self, itinerary: Itinerary) -> str:
        return self._template.render(view=build_view(itinerary))


class HtmlItineraryRenderer:
    def __init__(self) -> None:
        self._template = _environment().get_template("itinerary.html.j2")

    @property
    def format(self) -> RenderFormat:
        return RenderFormat.HTML

    @property
    def media_type(self) -> str:
        return "text/html"

    def render(self, itinerary: Itinerary) -> str:
        return self._template.render(view=build_view(itinerary))
