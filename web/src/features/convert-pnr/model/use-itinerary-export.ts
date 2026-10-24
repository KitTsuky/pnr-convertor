import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import type { ApiError } from "@/shared/api/api-error";

import { renderItinerary, type ConvertRequest } from "../api/convert-pnr";

// Long enough for the new tab to load the page before the blob URL is released.
const BLOB_URL_LIFETIME_MS = 60_000;

export function useCopyItineraryText() {
  return useMutation<unknown, ApiError, ConvertRequest>({
    mutationFn: async (request) => {
      const text = await renderItinerary(request, "text");
      await navigator.clipboard.writeText(text);
    },
    onSuccess: () => toast.success("Itinerary copied as text"),
    onError: (error) => toast.error(error.message),
  });
}

export function useOpenPrintableItinerary() {
  return useMutation<unknown, ApiError, ConvertRequest>({
    mutationFn: async (request) => {
      const html = await renderItinerary(request, "html");
      const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
      window.open(url, "_blank", "noopener");
      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, BLOB_URL_LIFETIME_MS);
    },
    onError: (error) => toast.error(error.message),
  });
}
