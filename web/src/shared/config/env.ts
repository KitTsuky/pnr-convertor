import { z } from "zod";

const envSchema = z.object({
  VITE_API_BASE_URL: z.union([z.literal(""), z.url()]).default(""),
});

// Fails fast at startup on a misconfigured build instead of on the first request.
export const env = envSchema.parse(import.meta.env);
