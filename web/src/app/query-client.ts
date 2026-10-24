import { QueryClient } from "@tanstack/react-query";

export function createQueryClient(): QueryClient {
  // Conversions are explicit user actions: never retry them silently.
  return new QueryClient({ defaultOptions: { mutations: { retry: false } } });
}
