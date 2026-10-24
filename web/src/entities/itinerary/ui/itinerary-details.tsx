import { Mail, Phone, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { formatIsoDate, passengerName, passengerType } from "../lib/format";
import { GDS_LABELS } from "../model/gds";
import type { Itinerary, Passenger, Segment } from "../model/schema";
import { FlightCard } from "./flight-card";
import { JourneyCard } from "./journey-card";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

interface ItineraryDetailsProps {
  itinerary: Itinerary;
  actions?: ReactNode;
}

export function ItineraryDetails({ itinerary, actions }: ItineraryDetailsProps) {
  const passengers = new Map(itinerary.passengers.map((p) => [p.index, p]));
  const segments = new Map(itinerary.segments.map((s) => [s.index, s]));
  const inJourneys = new Set(itinerary.journeys.flatMap((j) => j.segment_indexes));
  const cancelled = itinerary.segments.filter((s) => !inJourneys.has(s.index));

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Booking reference
            </p>
            <p className="font-mono text-2xl font-semibold tracking-widest">
              {itinerary.record_locator ?? "—"}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{GDS_LABELS[itinerary.gds]}</Badge>
            {actions}
          </div>
        </CardContent>
      </Card>

      {itinerary.warnings.length > 0 && (
        <Alert tone="warning">
          <TriangleAlert aria-hidden />
          <AlertTitle>Some lines could not be read</AlertTitle>
          <AlertDescription>
            <ul className="list-inside list-disc">
              {itinerary.warnings.map((w) => (
                <li key={`${w.line_number}-${w.message}`}>
                  Line {w.line_number}: {w.message}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {itinerary.passengers.length > 0 && <PassengersCard passengers={itinerary.passengers} />}

      {itinerary.journeys.map((journey, index) => (
        <JourneyCard
          key={journey.segment_indexes.join("-")}
          number={index + 1}
          journey={journey}
          segments={journey.segment_indexes
            .map((i) => segments.get(i))
            .filter((s): s is Segment => s !== undefined)}
          passengers={passengers}
        />
      ))}

      {cancelled.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Cancelled flights</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {cancelled.map((segment) => (
              <FlightCard key={segment.index} segment={segment} passengers={passengers} />
            ))}
          </CardContent>
        </Card>
      )}

      {itinerary.tickets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Tickets</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y text-sm">
              {itinerary.tickets.map((ticket) => {
                const holder =
                  ticket.passenger_index === null
                    ? undefined
                    : passengers.get(ticket.passenger_index);
                return (
                  <li key={ticket.number} className="flex flex-wrap justify-between gap-2 py-2">
                    <span className="font-mono font-medium">{ticket.number}</span>
                    <span className="text-muted-foreground">
                      {[
                        holder &&
                          (ticket.infant
                            ? `Infant of ${passengerName(holder)}`
                            : passengerName(holder)),
                        ticket.issue_date && `Issued ${formatIsoDate(ticket.issue_date)}`,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      )}

      {itinerary.contacts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Contacts</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2 text-sm">
              {itinerary.contacts.map((contact) => (
                <li key={`${contact.kind}-${contact.text}`} className="flex items-center gap-2">
                  {contact.kind === "email" ? (
                    <Mail className="size-4 text-muted-foreground" aria-label="Email" />
                  ) : (
                    <Phone className="size-4 text-muted-foreground" aria-label="Phone" />
                  )}
                  <span className="font-mono text-xs break-all">{contact.text}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PassengersCard({ passengers }: { passengers: readonly Passenger[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Passengers</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y text-sm">
          {passengers.map((p) => (
            <li key={p.index} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <span>
                <span className="text-muted-foreground tabular-nums">{p.index}.</span>{" "}
                <span className="font-medium">{passengerName(p)}</span>
                {p.infant && (
                  <span className="block text-xs text-muted-foreground">
                    with infant {p.infant.last_name}/{p.infant.first_name}
                    {p.infant.date_of_birth && `, born ${formatIsoDate(p.infant.date_of_birth)}`}
                  </span>
                )}
              </span>
              <Badge>{passengerType(p.type)}</Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
