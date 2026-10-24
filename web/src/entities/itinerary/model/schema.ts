import { z } from "zod";

/** Mirrors the API's public v1 contract (`ConvertResponse`). Unknown fields are ignored. */

export const gdsSchema = z.enum(["amadeus", "sabre", "galileo", "worldspan", "apollo"]);

const localDateTime = z.iso.datetime({ local: true });
const offsetDateTime = z.iso.datetime({ offset: true });
const isoDate = z.iso.date();

const distanceSchema = z.object({ km: z.number().int(), miles: z.number().int() });

const airportSchema = z.object({
  iata: z.string(),
  name: z.string(),
  city: z.string().nullable(),
  country: z.string(),
  timezone: z.string(),
  latitude: z.number(),
  longitude: z.number(),
});

const passengerSchema = z.object({
  index: z.number().int(),
  last_name: z.string(),
  first_name: z.string(),
  title: z.string().nullable(),
  type: z.string(),
  date_of_birth: isoDate.nullable(),
  infant: z
    .object({ last_name: z.string(), first_name: z.string(), date_of_birth: isoDate.nullable() })
    .nullable(),
});

export const statusCategorySchema = z.enum([
  "confirmed",
  "waitlisted",
  "requested",
  "cancelled",
  "unknown",
]);

const segmentSchema = z.object({
  index: z.number().int(),
  carrier: z.string(),
  flight_number: z.string(),
  booking_class: z.string(),
  origin: z.string(),
  destination: z.string(),
  departure_local: localDateTime,
  arrival_local: localDateTime,
  status: z.object({
    code: z.string(),
    category: statusCategorySchema,
    description: z.string().nullable(),
  }),
  passenger_count: z.number().int(),
  airline: z.object({ iata: z.string(), name: z.string() }).nullable(),
  operated_by: z.string().nullable(),
  origin_airport: airportSchema.nullable(),
  destination_airport: airportSchema.nullable(),
  departure_at: offsetDateTime.nullable(),
  arrival_at: offsetDateTime.nullable(),
  duration_minutes: z.number().int().nullable(),
  distance: distanceSchema.nullable(),
  seats: z.array(z.object({ passenger_index: z.number().int().nullable(), seat: z.string() })),
});

const journeySchema = z.object({
  segment_indexes: z.array(z.number().int()),
  origin: z.string(),
  destination: z.string(),
  departure_at: offsetDateTime.nullable(),
  arrival_at: offsetDateTime.nullable(),
  duration_minutes: z.number().int().nullable(),
  distance: distanceSchema.nullable(),
  connections: z.array(
    z.object({ airport: z.string(), duration_minutes: z.number().int().nullable() }),
  ),
});

const ticketSchema = z.object({
  number: z.string(),
  passenger_index: z.number().int().nullable(),
  issuing_airline: z.string().nullable(),
  issue_date: isoDate.nullable(),
  electronic: z.boolean(),
  infant: z.boolean(),
});

export const itinerarySchema = z.object({
  gds: gdsSchema,
  record_locator: z.string().nullable(),
  passengers: z.array(passengerSchema),
  segments: z.array(segmentSchema),
  journeys: z.array(journeySchema),
  tickets: z.array(ticketSchema),
  contacts: z.array(z.object({ kind: z.enum(["phone", "email"]), text: z.string() })),
  warnings: z.array(z.object({ line_number: z.number().int(), message: z.string() })),
});

export type Gds = z.infer<typeof gdsSchema>;
export type StatusCategory = z.infer<typeof statusCategorySchema>;
export type Itinerary = z.infer<typeof itinerarySchema>;
export type Passenger = Itinerary["passengers"][number];
export type Segment = Itinerary["segments"][number];
export type Journey = Itinerary["journeys"][number];
export type Airport = z.infer<typeof airportSchema>;
