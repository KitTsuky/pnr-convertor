import { AxiosError, AxiosHeaders, type AxiosResponse } from "axios";
import { z } from "zod";

import { ApiError, toApiError } from "./api-error";

const PROBLEM = {
  type: "about:blank#unsupported_format",
  title: "PNR could not be converted",
  status: 422,
  code: "unsupported_format",
  detail: "Could not recognize the PNR format.",
};

function axiosError(data: unknown, status = 422): AxiosError {
  const config = { headers: new AxiosHeaders() };
  const response = { data, status, statusText: "", headers: {}, config } as AxiosResponse;
  return new AxiosError("Request failed", "ERR_BAD_RESPONSE", config, null, response);
}

describe("toApiError", () => {
  it("reads RFC 9457 problem details", () => {
    const error = toApiError(axiosError(PROBLEM));
    expect(error).toMatchObject({ kind: "problem", message: PROBLEM.detail, problem: PROBLEM });
  });

  it("reads problem details sent as text to a text or HTML request", () => {
    expect(toApiError(axiosError(JSON.stringify(PROBLEM))).kind).toBe("problem");
  });

  it("reports an unexpected body with its status", () => {
    const error = toApiError(axiosError("<html>Bad gateway</html>", 502));
    expect(error).toMatchObject({ kind: "unexpected", message: "The API failed with status 502." });
  });

  it("reports a request that never got a response as a network error", () => {
    expect(toApiError(new AxiosError("Network Error", "ERR_NETWORK")).kind).toBe("network");
  });

  it("reports a response the schema rejects as a contract error", () => {
    const zodError = z.object({ a: z.string() }).safeParse({}).error;
    expect(toApiError(zodError).kind).toBe("contract");
  });

  it("keeps an ApiError and wraps anything else", () => {
    const original = new ApiError("network", "offline");
    expect(toApiError(original)).toBe(original);
    expect(toApiError(new Error("boom")).kind).toBe("unexpected");
  });
});
