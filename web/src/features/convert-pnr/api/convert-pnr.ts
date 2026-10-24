import { itinerarySchema, type Gds, type Itinerary } from "@/entities/itinerary";
import { toApiError } from "@/shared/api/api-error";
import { http } from "@/shared/api/http";

export interface ConvertRequest {
  pnr: string;
  gds?: Gds;
  reference_date?: string;
}

export type RenderFormat = "text" | "html";

export async function convertPnr(request: ConvertRequest): Promise<Itinerary> {
  try {
    const { data } = await http.post<unknown>("/v1/convert", request);
    return itinerarySchema.parse(data);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function renderItinerary(
  request: ConvertRequest,
  format: RenderFormat,
): Promise<string> {
  try {
    const { data } = await http.post<string>("/v1/convert", request, {
      params: { format },
      responseType: "text",
      headers: { Accept: format === "html" ? "text/html" : "text/plain" },
    });
    return data;
  } catch (error) {
    throw toApiError(error);
  }
}
