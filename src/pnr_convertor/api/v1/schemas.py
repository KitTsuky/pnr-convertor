"""Public v1 contract. Changing a field here is a breaking change for clients."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from pnr_convertor.domain.models import (
    FlightSegment,
    GdsFormat,
    ParsedPnr,
    ParseWarning,
    Passenger,
    SegmentStatusCategory,
)

MAX_PNR_LENGTH = 20_000


class _Schema(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ConvertRequest(_Schema):
    pnr: str = Field(
        min_length=1,
        max_length=MAX_PNR_LENGTH,
        description="Raw PNR text exactly as displayed by the GDS terminal.",
    )
    gds: GdsFormat | None = Field(default=None, description="Source format. Omit to auto-detect.")
    reference_date: date | None = Field(
        default=None,
        description=(
            "Date the PNR was displayed; used to infer years for dates like `15MAR`. "
            "Defaults to today (UTC)."
        ),
    )


class PassengerOut(_Schema):
    index: int
    last_name: str
    first_name: str
    title: str | None

    @classmethod
    def from_domain(cls, passenger: Passenger) -> PassengerOut:
        return cls(
            index=passenger.index,
            last_name=passenger.last_name,
            first_name=passenger.first_name,
            title=passenger.title,
        )


class SegmentStatusOut(_Schema):
    code: str
    category: SegmentStatusCategory


class FlightSegmentOut(_Schema):
    index: int
    carrier: str
    flight_number: str
    booking_class: str
    origin: str
    destination: str
    departure_local: datetime = Field(description="Local time at the origin airport.")
    arrival_local: datetime = Field(description="Local time at the destination airport.")
    status: SegmentStatusOut
    passenger_count: int

    @classmethod
    def from_domain(cls, segment: FlightSegment) -> FlightSegmentOut:
        return cls(
            index=segment.index,
            carrier=segment.carrier,
            flight_number=segment.flight_number,
            booking_class=segment.booking_class,
            origin=segment.origin,
            destination=segment.destination,
            departure_local=segment.departure,
            arrival_local=segment.arrival,
            status=SegmentStatusOut(code=segment.status.code, category=segment.status.category),
            passenger_count=segment.passenger_count,
        )


class WarningOut(_Schema):
    line_number: int
    message: str

    @classmethod
    def from_domain(cls, warning: ParseWarning) -> WarningOut:
        return cls(line_number=warning.line_number, message=warning.message)


class ConvertResponse(_Schema):
    gds: GdsFormat
    record_locator: str | None
    passengers: list[PassengerOut]
    segments: list[FlightSegmentOut]
    warnings: list[WarningOut]

    @classmethod
    def from_domain(cls, pnr: ParsedPnr) -> ConvertResponse:
        return cls(
            gds=pnr.gds,
            record_locator=pnr.record_locator,
            passengers=[PassengerOut.from_domain(p) for p in pnr.passengers],
            segments=[FlightSegmentOut.from_domain(s) for s in pnr.segments],
            warnings=[WarningOut.from_domain(w) for w in pnr.warnings],
        )
