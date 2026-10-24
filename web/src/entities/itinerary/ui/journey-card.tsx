import { Clock } from "lucide-react";
import { Fragment } from "react";

import { formatDate, formatDistance, formatDuration, placeName } from "../lib/format";
import type { Journey, Passenger, Segment } from "../model/schema";
import { FlightCard } from "./flight-card";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

interface JourneyCardProps {
  journey: Journey;
  number: number;
  segments: readonly Segment[];
  passengers: ReadonlyMap<number, Passenger>;
}

export function JourneyCard({ journey, number, segments, passengers }: JourneyCardProps) {
  const first = segments[0];
  const last = segments.at(-1);
  if (!first || !last) return null;

  const meta = [
    formatDate(first.departure_local),
    stopsLabel(journey),
    formatDuration(journey.duration_minutes),
    formatDistance(journey.distance),
  ].filter(Boolean);

  return (
    <Card>
      <CardHeader>
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Trip {number}
        </p>
        <CardTitle className="text-lg">
          {placeName(first.origin, first.origin_airport)} →{" "}
          {placeName(last.destination, last.destination_airport)}
        </CardTitle>
        <CardDescription>{meta.join(" · ")}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {segments.map((segment, index) => {
          const connection = journey.connections[index];
          const onward = segments[index + 1];
          return (
            <Fragment key={segment.index}>
              <FlightCard segment={segment} passengers={passengers} />
              {connection && onward && (
                <p className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
                  <Clock className="size-3.5" aria-hidden />
                  {[
                    formatDuration(connection.duration_minutes),
                    `connection in ${placeName(connection.airport, onward.origin_airport)} (${connection.airport})`,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                </p>
              )}
            </Fragment>
          );
        })}
      </CardContent>
    </Card>
  );
}

// A single segment may still land on the way (a technical stop): "direct", never "nonstop".
function stopsLabel(journey: Journey): string {
  const count = journey.connections.length;
  if (count === 0) return "Direct";
  const airports = journey.connections.map((c) => c.airport).join(", ");
  return `${count} connection${count > 1 ? "s" : ""} (${airports})`;
}
