import { useMutation } from "@tanstack/react-query";

import type { Itinerary } from "@/entities/itinerary";
import type { ApiError } from "@/shared/api/api-error";

import { convertPnr, type ConvertRequest } from "../api/convert-pnr";

export function useConvertPnr() {
  return useMutation<Itinerary, ApiError, ConvertRequest>({
    mutationKey: ["convert-pnr"],
    mutationFn: (request) => convertPnr(request),
  });
}
