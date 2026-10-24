import { z } from "zod";

import { gdsSchema } from "@/entities/itinerary";

import type { ConvertRequest } from "../api/convert-pnr";

/** Same limit as the API, so an oversized paste is caught before it is sent. */
export const MAX_PNR_LENGTH = 20_000;

export const AUTO_DETECT = "auto";

export const convertFormSchema = z.object({
  pnr: z
    .string()
    .trim()
    .min(1, "Paste a PNR to convert.")
    .max(
      MAX_PNR_LENGTH,
      `A PNR can be at most ${MAX_PNR_LENGTH.toLocaleString("en-GB")} characters.`,
    ),
  gds: z.union([z.literal(AUTO_DETECT), gdsSchema]),
  referenceDate: z.union([z.literal(""), z.iso.date("Use a valid date.")]),
});

export type ConvertFormValues = z.infer<typeof convertFormSchema>;

export const DEFAULT_VALUES: ConvertFormValues = { pnr: "", gds: AUTO_DETECT, referenceDate: "" };

export function toConvertRequest(values: ConvertFormValues): ConvertRequest {
  return {
    pnr: values.pnr,
    ...(values.gds !== AUTO_DETECT && { gds: values.gds }),
    ...(values.referenceDate && { reference_date: values.referenceDate }),
  };
}
