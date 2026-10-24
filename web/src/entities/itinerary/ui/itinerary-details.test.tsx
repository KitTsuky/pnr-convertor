import { render, screen, within } from "@testing-library/react";

import { readApiFixture } from "@/test/fixtures";

import { itinerarySchema, type Itinerary } from "../model/schema";
import { ItineraryDetails } from "./itinerary-details";

function fixture(gds: string, name: string): Itinerary {
  return itinerarySchema.parse(readApiFixture(gds, name));
}

describe("ItineraryDetails", () => {
  it("lists cancelled flights apart and marks arrivals on another day", () => {
    render(<ItineraryDetails itinerary={fixture("galileo", "statuses_children_and_infant")} />);

    const cancelled = screen.getByRole("heading", { name: "Cancelled flights" }).closest("section");
    expect(within(cancelled!).getByText("Cancelled")).toBeInTheDocument();
    expect(screen.getAllByTitle("Arrives on another day").map((el) => el.textContent)).toEqual([
      "+2",
      "+1",
    ]);
    expect(screen.getByText("Waitlisted")).toBeInTheDocument();
  });

  it("shows passengers with infants, tickets, seats and the codeshare operator", () => {
    render(<ItineraryDetails itinerary={fixture("amadeus", "children_and_infants")} />);
    expect(screen.getByText(/with infant POPESCU\/ILINCA, born/)).toBeInTheDocument();
    expect(screen.getByText(/Infant of POPESCU\/ANDREI MR/)).toBeInTheDocument();

    render(<ItineraryDetails itinerary={fixture("apollo", "overnight_codeshare_connection")} />);
    expect(screen.getByText("Operated by BRUSSELS AIRLINES")).toBeInTheDocument();
  });

  it("warns about lines the API skipped", () => {
    const itinerary = {
      ...fixture("amadeus", "basic_return"),
      warnings: [{ line_number: 4, message: "Skipped air segment: Malformed GDS date" }],
    };
    render(<ItineraryDetails itinerary={itinerary} />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Line 4: Skipped air segment: Malformed GDS date",
    );
  });

  it("renders the actions it is given", () => {
    render(
      <ItineraryDetails
        itinerary={fixture("amadeus", "basic_return")}
        actions={<button type="button">Share</button>}
      />,
    );
    expect(screen.getByRole("button", { name: "Share" })).toBeInTheDocument();
  });
});
