import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SkipLink } from "@/components/ui/skip-link";
import { EmptyState } from "@/components/states/EmptyState";

expect.extend(toHaveNoViolations);

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

  it("icon-only button has aria-label and passes axe", async () => {
    const { container } = render(
      <Button size="icon" aria-label="Close dialog">
        <span aria-hidden>×</span>
      </Button>,
    );

    expect(screen.getByRole("button", { name: /close dialog/i })).toBeInTheDocument();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("input with label passes axe", async () => {
    const { container } = render(
      <div>
        <Label htmlFor="email">Email address</Label>
        <Input id="email" type="email" placeholder="you@example.com" />
      </div>,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("dialog has accessible title and passes axe", async () => {
    const { container } = render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogDescription>
              Are you sure you want to proceed?
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /confirm action/i })).toBeInTheDocument();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("select has listbox role and passes axe", async () => {
    const { container } = render(
      <Select>
        <SelectTrigger aria-label="Choose a fruit">
          <SelectValue placeholder="Select a fruit" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="apple">Apple</SelectItem>
          <SelectItem value="banana">Banana</SelectItem>
        </SelectContent>
      </Select>,
    );

    expect(screen.getByRole("combobox")).toBeInTheDocument();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("skip link is focusable and passes axe", async () => {
    const { container } = render(
      <>
        <SkipLink targetId="content" />
        <main id="content" tabIndex={-1}>
          <h1>Page content</h1>
        </main>
      </>,
    );

    const skipLink = screen.getByRole("link", { name: /skip to content/i });
    expect(skipLink).toBeInTheDocument();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("empty state passes axe", async () => {
    const { container } = render(
      <EmptyState
        title="No items"
        description="There are no items to display."
        action={<Button>Create item</Button>}
      />,
    );

    expect(screen.getByRole("heading", { name: /no items/i })).toBeInTheDocument();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
