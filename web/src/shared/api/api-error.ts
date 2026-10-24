import axios from "axios";
import { z } from "zod";

/** RFC 9457 problem details, as returned by the API for every failure. */
export const problemSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number().int(),
  detail: z.string(),
  code: z.string(),
});

export type Problem = z.infer<typeof problemSchema>;

export type ApiErrorKind = "problem" | "network" | "contract" | "unexpected";

export class ApiError extends Error {
  override readonly name = "ApiError";

  constructor(
    readonly kind: ApiErrorKind,
    message: string,
    readonly problem?: Problem,
  ) {
    super(message);
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (error instanceof z.ZodError) {
    return new ApiError("contract", "The API returned a response this app does not understand.");
  }
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return new ApiError("network", "Can't reach the PNR Convertor API. Check your connection.");
    }
    const problem = problemSchema.safeParse(parseBody(error.response.data));
    if (problem.success) return new ApiError("problem", problem.data.detail, problem.data);
    return new ApiError("unexpected", `The API failed with status ${error.response.status}.`);
  }
  return new ApiError("unexpected", "Something went wrong. Please try again.");
}

// Text and HTML requests receive their error body as a string.
function parseBody(data: unknown): unknown {
  if (typeof data !== "string") return data;
  try {
    return JSON.parse(data) as unknown;
  } catch {
    return data;
  }
}
