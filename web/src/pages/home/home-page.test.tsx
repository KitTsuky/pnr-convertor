import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse, type JsonBodyType } from "msw";

import { readApiFixture } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { HomePage } from "./home-page";

const CONVERT_URL = "*/v1/convert";
const ITINERARY = readApiFixture("amadeus", "connection_via_hub") as JsonBodyType;

function setup() {
  const user = userEvent.setup();
  renderWithProviders(<HomePage />);
  return { user, pnrField: screen.getByLabelText("PNR") };
}

describe("HomePage", () => {
  it("converts a pasted PNR and shows the itinerary", async () => {
    const requests: unknown[] = [];
    server.use(
      http.post(CONVERT_URL, async ({ request }) => {
        requests.push(await request.json());
        return HttpResponse.json(ITINERARY);
      }),
    );
    const { user } = setup();

    await user.click(screen.getByRole("button", { name: "Try an example" }));
    await user.click(screen.getByRole("button", { name: "Convert" }));

    expect(await screen.findByText("M8RT5V")).toBeInTheDocument();
    expect(requests).toEqual([{ pnr: expect.stringContaining("M8RT5V") as unknown }]);
    expect(
      screen.getAllByRole("heading", { name: /Bucharest → Dubai|Dubai → Bucharest/ }),
    ).toHaveLength(2);
    const firstFlight = screen.getByRole("article", { name: "Flight TK 1046" });
    expect(within(firstFlight).getByText("09:05")).toBeInTheDocument();
    expect(within(firstFlight).getByText("Confirmed")).toBeInTheDocument();
    expect(screen.getAllByText(/2h 45m connection in Istanbul \(IST\)/)).toHaveLength(2);
  });

  it("submits with Ctrl+Enter from the PNR field", async () => {
    server.use(http.post(CONVERT_URL, () => HttpResponse.json(ITINERARY)));
    const { user, pnrField } = setup();

    await user.type(pnrField, "RP/ABC");
    await user.keyboard("{Control>}{Enter}{/Control}");

    expect(await screen.findByText("M8RT5V")).toBeInTheDocument();
  });

  it("validates an empty PNR without calling the API", async () => {
    const { user, pnrField } = setup();

    await user.click(screen.getByRole("button", { name: "Convert" }));

    expect(await screen.findByText("Paste a PNR to convert.")).toBeInTheDocument();
    expect(pnrField).toHaveAttribute("aria-invalid", "true");
  });

  it("shows the API's problem details", async () => {
    server.use(
      http.post(CONVERT_URL, () =>
        HttpResponse.json(
          {
            type: "about:blank#unsupported_format",
            title: "PNR could not be converted",
            status: 422,
            code: "unsupported_format",
            detail: "Could not recognize the PNR format.",
          },
          { status: 422, headers: { "content-type": "application/problem+json" } },
        ),
      ),
    );
    const { user, pnrField } = setup();

    await user.type(pnrField, "not a pnr");
    await user.click(screen.getByRole("button", { name: "Convert" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("PNR could not be converted");
    expect(alert).toHaveTextContent("Could not recognize the PNR format.");
  });

  it("explains when the API cannot be reached", async () => {
    server.use(http.post(CONVERT_URL, () => HttpResponse.error()));
    const { user, pnrField } = setup();

    await user.type(pnrField, "RP/ABC");
    await user.click(screen.getByRole("button", { name: "Convert" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Can't reach the PNR Convertor API");
  });

  it("copies the itinerary as text", async () => {
    server.use(
      http.post(CONVERT_URL, ({ request }) =>
        new URL(request.url).searchParams.get("format") === "text"
          ? HttpResponse.text("FLIGHT ITINERARY\nBooking reference: M8RT5V\n")
          : HttpResponse.json(ITINERARY),
      ),
    );
    const { user, pnrField } = setup();

    await user.type(pnrField, "RP/ABC");
    await user.click(screen.getByRole("button", { name: "Convert" }));
    await user.click(await screen.findByRole("button", { name: "Copy text" }));

    expect(await screen.findByText("Itinerary copied as text")).toBeInTheDocument();
    expect(await navigator.clipboard.readText()).toBe(
      "FLIGHT ITINERARY\nBooking reference: M8RT5V\n",
    );
  });

  it("clears the form and the result", async () => {
    server.use(http.post(CONVERT_URL, () => HttpResponse.json(ITINERARY)));
    const { user, pnrField } = setup();

    await user.type(pnrField, "RP/ABC");
    await user.click(screen.getByRole("button", { name: "Convert" }));
    await screen.findByText("M8RT5V");
    await user.click(screen.getByRole("button", { name: "Clear" }));

    expect(pnrField).toHaveValue("");
    expect(screen.getByText("Your itinerary will appear here")).toBeInTheDocument();
  });
});
