import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  EntityBadge,
  StatusBadge,
  MetricCard,
  PageHeader,
  SectionCard,
  Btn,
  Tabs,
  type EntityType,
  type StatusType,
} from "./WfPrimitives";

describe("WfPrimitives", () => {
  describe("EntityBadge", () => {
    const entityTypes: EntityType[] = [
      "capability",
      "usecase",
      "persona",
      "valuedriver",
    ];

    it("should render all entity types with correct default labels", () => {
      const expectedLabels: Record<EntityType, string> = {
        capability: "Capability",
        usecase: "Use Case",
        persona: "Persona",
        valuedriver: "Value Driver",
      };

      entityTypes.forEach((type) => {
        const { container } = render(<EntityBadge type={type} />);
        expect(container.textContent).toBe(expectedLabels[type]);
      });
    });

    it("should render custom label when provided", () => {
      render(<EntityBadge type="capability" label="Custom Label" />);
      expect(screen.getByText("Custom Label")).toBeInTheDocument();
    });

    it("should render as a semantic span element", () => {
      const { container } = render(<EntityBadge type="capability" />);
      const badge = container.firstElementChild;
      expect(badge?.tagName.toLowerCase()).toBe("span");
      expect(badge?.textContent).toBe("Capability");
    });
  });

  describe("StatusBadge", () => {
    const statusTypes: StatusType[] = [
      "completed",
      "running",
      "processing",
      "failed",
      "paused",
      "pending",
      "cancelled",
    ];

    it("should render all status types with correct icons", () => {
      const expectedIcons: Record<StatusType, string> = {
        completed: "✓",
        running: "↻",
        processing: "↻",
        failed: "✕",
        paused: "⏸",
        pending: "…",
        cancelled: "⊘",
      };

      statusTypes.forEach((status) => {
        const { container } = render(<StatusBadge status={status} />);
        expect(container.textContent).toContain(expectedIcons[status]);
        expect(container.textContent).toContain(
          status.charAt(0).toUpperCase() + status.slice(1)
        );
      });
    });

    it("should render as a semantic span element", () => {
      const { container } = render(<StatusBadge status="completed" />);
      const badge = container.firstElementChild;
      expect(badge?.tagName.toLowerCase()).toBe("span");
      expect(badge?.textContent).toContain("Completed");
      expect(badge?.textContent).toContain("✓");
    });
  });

  describe("MetricCard", () => {
    it("should render label and value", () => {
      render(<MetricCard label="Revenue" value="$1.2M" />);

      expect(screen.getByText("Revenue")).toBeInTheDocument();
      expect(screen.getByText("$1.2M")).toBeInTheDocument();
    });

    it("should render trend when provided without trendUp", () => {
      render(<MetricCard label="Users" value="1,234" trend="+12% vs last month" />);

      expect(screen.getByText("+12% vs last month")).toBeInTheDocument();
    });

    it("should render trend with arrow when trendUp is true", () => {
      render(
        <MetricCard
          label="Growth"
          value="25%"
          trend="vs last quarter"
          trendUp={true}
        />
      );

      expect(screen.getByText("↗ vs last quarter")).toBeInTheDocument();
    });

    it("should indicate positive trend when trendUp is true", () => {
      render(<MetricCard label="Test" value="100" trend="+5%" trendUp={true} />);
      expect(screen.getByText("↗ +5%")).toBeInTheDocument();
    });

    it("should show trend without indicator when trendUp is not provided", () => {
      render(<MetricCard label="Test" value="100" trend="No change" />);
      expect(screen.getByText("No change")).toBeInTheDocument();
      // Should NOT have the up arrow
      expect(screen.queryByText("↗ No change")).not.toBeInTheDocument();
    });

    it("should not render trend section when trend is not provided", () => {
      const { container } = render(<MetricCard label="Static" value="100" />);
      // The card should only contain label and value
      expect(screen.getByText("Static")).toBeInTheDocument();
      expect(screen.getByText("100")).toBeInTheDocument();
      // Container should have exactly 2 children (label row + value row)
      const cardContent = container.firstElementChild;
      expect(cardContent?.children.length).toBe(2);
    });
  });

  describe("PageHeader", () => {
    it("should render title", () => {
      render(<PageHeader title="Dashboard" />);
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });

    it("should render subtitle when provided", () => {
      render(<PageHeader title="Dashboard" subtitle="Overview page" />);
      expect(screen.getByText("Overview page")).toBeInTheDocument();
    });

    it("should render breadcrumbs when provided", () => {
      render(
        <PageHeader
          title="Final Page"
          breadcrumbs={["Home", "Section", "Final Page"]}
        />
      );

      expect(screen.getByText("Home")).toBeInTheDocument();
      expect(screen.getByText("Section")).toBeInTheDocument();
      // Title and last breadcrumb share text - use container query
      const title = screen.getAllByText("Final Page").find(
        el => el.tagName.toLowerCase() === "h1"
      );
      expect(title).toBeInTheDocument();
    });

    it("should render actions when provided", () => {
      render(
        <PageHeader
          title="Page"
          actions={<button>Action</button>}
        />
      );

      expect(screen.getByText("Action")).toBeInTheDocument();
    });
  });

  describe("SectionCard", () => {
    it("should render title", () => {
      render(<SectionCard title="Section Title">Content</SectionCard>);
      expect(screen.getByText("Section Title")).toBeInTheDocument();
    });

    it("should render children content", () => {
      render(<SectionCard title="Test">Child Content</SectionCard>);
      expect(screen.getByText("Child Content")).toBeInTheDocument();
    });

    it("should render without title", () => {
      render(<SectionCard>Content without title</SectionCard>);
      expect(screen.getByText("Content without title")).toBeInTheDocument();
    });

    it("should render with custom className", () => {
      const { container } = render(
        <SectionCard className="custom-class">Content</SectionCard>
      );
      // Verify the card is in the document with custom class
      expect(screen.getByText("Content")).toBeInTheDocument();
      expect(container.querySelector(".custom-class")).toBeInTheDocument();
    });
  });

  describe("Btn", () => {
    it("should render children", () => {
      render(<Btn>Click Me</Btn>);
      expect(screen.getByText("Click Me")).toBeInTheDocument();
    });

    it("should render button with accessible role", () => {
      render(<Btn variant="primary">Click Me</Btn>);
      expect(screen.getByRole("button", { name: "Click Me" })).toBeInTheDocument();
    });

    it("should call onClick when clicked", () => {
      const handleClick = vi.fn();
      render(<Btn onClick={handleClick}>Click</Btn>);

      screen.getByText("Click").click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("should be disabled when disabled prop is true", () => {
      render(<Btn disabled>Disabled</Btn>);
      expect(screen.getByText("Disabled")).toBeDisabled();
    });
  });

  describe("Tabs", () => {
    const tabs = ["Tab 1", "Tab 2", "Tab 3"];

    it("should render all tabs", () => {
      render(<Tabs tabs={tabs} active="Tab 1" onChange={() => {}} />);

      tabs.forEach((tab) => {
        expect(screen.getByText(tab)).toBeInTheDocument();
      });
    });

    it("should mark active tab with aria-selected", () => {
      render(<Tabs tabs={tabs} active="Tab 2" onChange={() => {}} />);
      const buttons = screen.getAllByRole("tab");
      expect(buttons[1]).toHaveAttribute("aria-selected", "true");
      expect(buttons[0]).toHaveAttribute("aria-selected", "false");
      expect(buttons[2]).toHaveAttribute("aria-selected", "false");
    });

    it("should call onChange with clicked tab", () => {
      const handleChange = vi.fn();
      render(<Tabs tabs={tabs} active="Tab 1" onChange={handleChange} />);

      screen.getByText("Tab 2").click();
      expect(handleChange).toHaveBeenCalledWith("Tab 2");
    });
  });
});
