import {
  dayDifference,
  formatDate,
  formatDistance,
  formatDuration,
  formatIsoDate,
  formatTime,
  passengerName,
  passengerType,
  placeName,
} from "./format";

describe("itinerary formatting", () => {
  it("formats local date-times exactly as given, whatever the browser timezone", () => {
    expect(formatDate("2026-03-15T07:10:00")).toBe("Sun, 15 Mar 2026");
    expect(formatTime("2026-03-15T07:10:00")).toBe("07:10");
    expect(formatIsoDate("2025-02-28")).toBe("Fri, 28 Feb 2025");
  });

  it.each([
    ["2026-03-15T23:40:00", "2026-03-16T06:45:00", 1],
    ["2026-03-15T07:10:00", "2026-03-15T09:20:00", 0],
    ["2026-01-20T09:50:00", "2026-01-19T06:15:00", -1],
    ["2025-12-31T22:00:00", "2026-01-02T06:00:00", 2],
  ])("day difference %s → %s is %i", (from, to, days) => {
    expect(dayDifference(from, to)).toBe(days);
  });

  it.each([
    [null, null],
    [45, "45m"],
    [60, "1h 00m"],
    [495, "8h 15m"],
  ])("duration %s → %s", (minutes, label) => {
    expect(formatDuration(minutes)).toBe(label);
  });

  it("formats distances and names", () => {
    expect(formatDistance({ km: 12455, miles: 7739 })).toBe("12,455 km");
    expect(formatDistance(null)).toBeNull();
    expect(passengerName({ last_name: "DOE", first_name: "JANE", title: "MRS" })).toBe(
      "DOE/JANE MRS",
    );
    expect(passengerName({ last_name: "DOE", first_name: "TOM", title: null })).toBe("DOE/TOM");
    expect(passengerType("INS")).toBe("Infant with seat");
    expect(passengerType("STU")).toBe("STU");
    expect(placeName("ZZZ", null)).toBe("ZZZ");
  });
});
