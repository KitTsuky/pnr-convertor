import { env } from "@/shared/config/env";

/** Absolute URL of an API path, e.g. a logo, for elements the browser loads itself. */
export function apiUrl(path: string): string {
  return new URL(path, env.VITE_API_BASE_URL || window.location.origin).toString();
}
