import { listApiFixtures, readApiFixture } from "@/test/fixtures";

import { itinerarySchema } from "./schema";

const fixtures = listApiFixtures();

describe("itinerary schema matches the API contract", () => {
  it("covers every golden response", () => {
    expect(fixtures.length).toBeGreaterThanOrEqual(20);
  });

  // Parsing strips fields the schema does not know: equality proves nothing was dropped.
  it.each(fixtures)("$id", ({ gds, name }) => {
    const response = readApiFixture(gds, name);
    expect(itinerarySchema.parse(response)).toStrictEqual(response);
  });
});
