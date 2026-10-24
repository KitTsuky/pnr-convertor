import { fireEvent, render, screen } from "@testing-library/react";

import { AirlineLogo } from "./airline-logo";

describe("AirlineLogo", () => {
  it("shows the logo from the API", () => {
    render(<AirlineLogo code="TK" name="Turkish Airlines" logoUrl="/v1/airlines/TK/logo" />);

    const logo = screen.getByRole("img", { name: "Turkish Airlines" });
    expect(logo).toHaveAttribute("src", "http://localhost:3000/v1/airlines/TK/logo");
  });

  it("falls back to the airline code without a logo", () => {
    render(<AirlineLogo code="Q9" name="Q9" logoUrl={null} />);
    expect(screen.getByRole("img", { name: "Q9" })).toHaveTextContent("Q9");
  });

  it("falls back to the airline code when the logo fails to load", () => {
    render(<AirlineLogo code="TK" name="Turkish Airlines" logoUrl="/v1/airlines/TK/logo" />);

    fireEvent.error(screen.getByRole("img", { name: "Turkish Airlines" }));

    expect(screen.getByRole("img", { name: "Turkish Airlines" })).toHaveTextContent("TK");
  });
});
