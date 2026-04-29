import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

describe("component accessibility smoke tests", () => {
  it("button and input expose accessible roles and labels", () => {
    render(
      <main>
        <h1>Accessibility fixture</h1>
        <label htmlFor="customer-name">Customer name</label>
        <Input id="customer-name" placeholder="Type a name" />
        <Button type="button">Save</Button>
      </main>,
    );

    expect(screen.getByRole("heading", { name: /accessibility fixture/i })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /customer name/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });
});
