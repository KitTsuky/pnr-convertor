import { Plane } from "lucide-react";

import {
  dayDifference,
  formatDistance,
  formatDuration,
  formatShortDate,
  formatTime,
  passengerName,
  placeName,
} from "../lib/format";
import type { Passenger, Segment } from "../model/schema";
import { StatusBadge } from "./status-badge";

interface FlightCardProps {
  segment: Segment;
  passengers: ReadonlyMap<number, Passenger>;
}

export function FlightCard({ segment, passengers }: FlightCardProps) {
  const dayShift = dayDifference(segment.departure_local, segment.arrival_local);
  const facts = [formatDuration(segment.duration_minutes), formatDistance(segment.distance)].filter(
    Boolean,
  );
  const seats = segment.seats.map(({ seat, passenger_index }) => {
    const holder = passenger_index === null ? undefined : passengers.get(passenger_index);
    return holder ? `${seat} ${passengerName(holder)}` : seat;
  });

  return (
    <article
      className="rounded-lg border p-4"
      aria-label={`Flight ${segment.carrier} ${segment.flight_number}`}
    >
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-sm font-semibold">
            {segment.carrier} {segment.flight_number}
          </span>
          <span className="text-sm text-muted-foreground">
            {segment.airline?.name ?? segment.carrier}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Class {segment.booking_class}</span>
          <StatusBadge {...segment.status} />
        </div>
      </header>

      <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-start gap-3">
        <Stop
          time={formatTime(segment.departure_local)}
          date={formatShortDate(segment.departure_local)}
          code={segment.origin}
          place={placeName(segment.origin, segment.origin_airport)}
          airport={segment.origin_airport?.name}
        />
        <div className="flex min-w-20 flex-col items-center gap-1 pt-2 text-xs text-muted-foreground">
          <div className="flex w-full items-center gap-1">
            <span className="h-px flex-1 bg-border" />
            <Plane className="size-3.5" aria-hidden />
            <span className="h-px flex-1 bg-border" />
          </div>
          {facts.map((fact) => (
            <span key={fact}>{fact}</span>
          ))}
        </div>
        <Stop
          align="end"
          time={formatTime(segment.arrival_local)}
          dayShift={dayShift}
          date={formatShortDate(segment.arrival_local)}
          code={segment.destination}
          place={placeName(segment.destination, segment.destination_airport)}
          airport={segment.destination_airport?.name}
        />
      </div>

      {(segment.operated_by ?? seats.length > 0) && (
        <footer className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t pt-3 text-xs text-muted-foreground">
          {segment.operated_by && <span>Operated by {segment.operated_by}</span>}
          {seats.length > 0 && <span>Seats {seats.join(", ")}</span>}
        </footer>
      )}
    </article>
  );
}

interface StopProps {
  time: string;
  date: string;
  code: string;
  place: string;
  airport: string | undefined;
  dayShift?: number;
  align?: "start" | "end";
}

function Stop({ time, date, code, place, airport, dayShift = 0, align = "start" }: StopProps) {
  return (
    <div className={align === "end" ? "text-right" : undefined}>
      <p className="text-2xl font-semibold tracking-tight tabular-nums">
        {time}
        {dayShift !== 0 && (
          <sup className="ml-0.5 text-xs font-medium text-warning" title="Arrives on another day">
            {dayShift > 0 ? `+${dayShift}` : dayShift}
          </sup>
        )}
      </p>
      <p className="text-xs text-muted-foreground">{date}</p>
      <p className="mt-1 text-sm font-medium">
        {place} <span className="font-mono text-muted-foreground">{code}</span>
      </p>
      {airport && <p className="text-xs text-muted-foreground">{airport}</p>}
    </div>
  );
}
