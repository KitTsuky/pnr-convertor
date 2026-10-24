import type { Airport, Passenger, StatusCategory } from "../model/schema";

// API local times carry no offset; formatting them in UTC shows them exactly as given.
const dateFormat = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});
const shortDateFormat = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  day: "2-digit",
  month: "short",
  timeZone: "UTC",
});
const numberFormat = new Intl.NumberFormat("en-GB");

const PASSENGER_TYPES: Record<string, string> = {
  ADT: "Adult",
  CHD: "Child",
  CNN: "Child",
  INF: "Infant",
  INS: "Infant with seat",
  YTH: "Youth",
  SRC: "Senior",
  MIL: "Military",
  GOV: "Government",
};

export const STATUS_LABELS: Record<StatusCategory, string> = {
  confirmed: "Confirmed",
  waitlisted: "Waitlisted",
  requested: "Requested",
  cancelled: "Cancelled",
  unknown: "Unknown",
};

function asUtc(local: string): Date {
  return new Date(`${local.slice(0, 19)}Z`);
}

export function formatDate(local: string): string {
  return dateFormat.format(asUtc(local));
}

export function formatShortDate(local: string): string {
  return shortDateFormat.format(asUtc(local));
}

export function formatTime(local: string): string {
  return local.slice(11, 16);
}

/** Calendar days between two local date-times, e.g. `+1` for an overnight arrival. */
export function dayDifference(fromLocal: string, toLocal: string): number {
  const day = (local: string) => Date.parse(`${local.slice(0, 10)}T00:00:00Z`);
  return Math.round((day(toLocal) - day(fromLocal)) / 86_400_000);
}

export function formatDuration(minutes: number | null): string | null {
  if (minutes === null) return null;
  const hours = Math.floor(minutes / 60);
  const rest = String(minutes % 60).padStart(2, "0");
  return hours > 0 ? `${hours}h ${rest}m` : `${minutes}m`;
}

export function formatDistance(distance: { km: number; miles: number } | null): string | null {
  if (distance === null) return null;
  return `${numberFormat.format(distance.km)} km`;
}

export function placeName(code: string, airport: Airport | null): string {
  return airport?.city ?? code;
}

export function passengerName(passenger: Pick<Passenger, "last_name" | "first_name" | "title">) {
  return [`${passenger.last_name}/${passenger.first_name}`, passenger.title]
    .filter(Boolean)
    .join(" ");
}

export function passengerType(code: string): string {
  return PASSENGER_TYPES[code] ?? code;
}

export function formatIsoDate(isoDate: string): string {
  return formatDate(`${isoDate}T00:00:00`);
}
