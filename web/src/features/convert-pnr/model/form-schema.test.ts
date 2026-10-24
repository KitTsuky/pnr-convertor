import { convertFormSchema, DEFAULT_VALUES, MAX_PNR_LENGTH, toConvertRequest } from "./form-schema";

describe("convert form", () => {
  it("rejects an empty or oversized PNR", () => {
    const empty = convertFormSchema.safeParse({ ...DEFAULT_VALUES, pnr: "   " });
    const oversized = convertFormSchema.safeParse({
      ...DEFAULT_VALUES,
      pnr: "X".repeat(MAX_PNR_LENGTH + 1),
    });

    expect(empty.error?.issues[0]?.message).toBe("Paste a PNR to convert.");
    expect(oversized.success).toBe(false);
  });

  it("rejects an unknown format and a malformed date", () => {
    expect(convertFormSchema.safeParse({ ...DEFAULT_VALUES, pnr: "x", gds: "pars" }).success).toBe(
      false,
    );
    expect(
      convertFormSchema.safeParse({ ...DEFAULT_VALUES, pnr: "x", referenceDate: "2026-13-01" })
        .success,
    ).toBe(false);
  });

  it("sends only the fields the user set", () => {
    expect(toConvertRequest({ pnr: "PNR", gds: "auto", referenceDate: "" })).toStrictEqual({
      pnr: "PNR",
    });
    expect(
      toConvertRequest({ pnr: "PNR", gds: "sabre", referenceDate: "2026-01-15" }),
    ).toStrictEqual({ pnr: "PNR", gds: "sabre", reference_date: "2026-01-15" });
  });
});
