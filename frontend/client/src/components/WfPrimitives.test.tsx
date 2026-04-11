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

    it("should apply correct styling for capability", () => {
      const { container } = render(<EntityBadge type="capability" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-violet-100");
      expect(badge.className).toContain("text-violet-800");
      expect(badge.className).toContain("border-violet-200");
    });

    it("should apply correct styling for usecase", () => {
      const { container } = render(<EntityBadge type="usecase" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-cyan-100");
      expect(badge.className).toContain("text-cyan-800");
      expect(badge.className).toContain("border-cyan-200");
    });

    it("should apply correct styling for persona", () => {
      const { container } = render(<EntityBadge type="persona" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-amber-100");
      expect(badge.className).toContain("text-amber-800");
      expect(badge.className).toContain("border-amber-200");
    });

    it("should apply correct styling for valuedriver", () => {
      const { container } = render(<EntityBadge type="valuedriver" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-emerald-100");
      expect(badge.className).toContain("text-emerald-800");
      expect(badge.className).toContain("border-emerald-200");
    });

    it("should have correct base styling classes", () => {
      const { container } = render(<EntityBadge type="capability" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("inline-flex");
      expect(badge.className).toContain("items-center");
      expect(badge.className).toContain("gap-1");
      expect(badge.className).toContain("px-2");
      expect(badge.className).toContain("py-0.5");
      expect(badge.className).toContain("rounded-full");
      expect(badge.className).toContain("text-[10px]");
      expect(badge.className).toContain("font-semibold");
      expect(badge.className).toContain("border");
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

    it("should apply correct styling for completed", () => {
      const { container } = render(<StatusBadge status="completed" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-emerald-100");
      expect(badge.className).toContain("text-emerald-800");
      expect(badge.className).toContain("border-emerald-200");
    });

    it("should apply correct styling for running", () => {
      const { container } = render(<StatusBadge status="running" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-amber-100");
      expect(badge.className).toContain("text-amber-800");
      expect(badge.className).toContain("border-amber-200");
    });

    it("should apply same styling for processing as running", () => {
      const { container: running } = render(<StatusBadge status="running" />);
      const { container: processing } = render(
        <StatusBadge status="processing" />
      );

      expect(running.firstChild?.className).toBe(
        processing.firstChild?.className
      );
    });

    it("should apply correct styling for failed", () => {
      const { container } = render(<StatusBadge status="failed" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-red-100");
      expect(badge.className).toContain("text-red-800");
      expect(badge.className).toContain("border-red-200");
    });

    it("should apply correct styling for paused", () => {
      const { container } = render(<StatusBadge status="paused" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-neutral-100");
      expect(badge.className).toContain("text-neutral-600");
      expect(badge.className).toContain("border-neutral-200");
    });

    it("should apply correct styling for pending", () => {
      const { container } = render(<StatusBadge status="pending" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-blue-100");
      expect(badge.className).toContain("text-blue-800");
      expect(badge.className).toContain("border-blue-200");
    });

    it("should apply correct styling for cancelled", () => {
      const { container } = render(<StatusBadge status="cancelled" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("bg-gray-100");
      expect(badge.className).toContain("text-gray-600");
      expect(badge.className).toContain("border-gray-200");
    });

    it("should have correct base styling classes", () => {
      const { container } = render(<StatusBadge status="completed" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain("inline-flex");
      expect(badge.className).toContain("items-center");
      expect(badge.className).toContain("gap-1");
      expect(badge.className).toContain("px-2");
      expect(badge.className).toContain("py-0.5");
      expect(badge.className).toContain("rounded-full");
      expect(badge.className).toContain("text-[10px]");
      expect(badge.className).toContain("font-semibold");
      expect(badge.className).toContain("border");
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

    it("should apply green color when trendUp is true", () => {
      const { container } = render(
        <MetricCard label="Test" value="100" trend="+5%" trendUp={true} />
      );

      const trendElement = container.querySelector(".text-emerald-600");
      expect(trendElement).toBeInTheDocument();
    });

    it("should apply neutral color when trendUp is not provided", () => {
      const { container } = render(
        <MetricCard label="Test" value="100" trend="No change" />
      );

      const trendElement = container.querySelector(".text-neutral-500");
      expect(trendElement).toBeInTheDocument();
    });

    it("should not render trend section when trend is not provided", () => {
      const { container } = render(<MetricCard label="Static" value="100" />);

      const trendElement = container.querySelector(".text-emerald-600, .text-neutral-500");
      expect(trendElement).toBeNull();
    });

    it("should have correct container styling", () => {
      const { container } = render(<MetricCard label="Test" value="100" />);

      const card = container.firstChild as HTMLElement;
      expect(card.className).toContain("bg-white");
      expect(card.className).toContain("border");
      expect(card.className).toContain("border-neutral-200");
      expect(card.className).toContain("rounded-lg");
      expect(card.className).toContain("p-4");
      expect(card.className).toContain("flex-1");
    });

    it("should render large value with correct styling", () => {
      render(<MetricCard label="Revenue" value="$900,000.00" />);

      const value = screen.getByText("$900,000.00");
      expect(value.className).toContain("text-[26px]");
      expect(value.className).toContain("font-extrabold");
      expect(value.className).toContain("text-neutral-900");
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

    it("should apply custom className", () => {
      const { container } = render(
        <SectionCard className="custom-class">Content</SectionCard>
      );
      expect(container.firstChild?.className).toContain("custom-class");
    });
  });

  describe("Btn", () => {
    it("should render children", () => {
      render(<Btn>Click Me</Btn>);
      expect(screen.getByText("Click Me")).toBeInTheDocument();
    });

    it("should apply primary variant styling", () => {
      const { container } = render(<Btn variant="primary">Primary</Btn>);
      const button = container.firstChild as HTMLElement;
      expect(button.className).toContain("bg-blue-700");
      expect(button.className).toContain("text-white");
    });

    it("should apply ghost variant styling", () => {
      const { container } = render(<Btn variant="ghost">Ghost</Btn>);
      const button = container.firstChild as HTMLElement;
      expect(button.className).toContain("bg-white");
      expect(button.className).toContain("text-neutral-600");
    });

    it("should apply outline variant styling", () => {
      const { container } = render(<Btn variant="outline">Outline</Btn>);
      const button = container.firstChild as HTMLElement;
      expect(button.className).toContain("bg-transparent");
      expect(button.className).toContain("border-neutral-300");
    });

    it("should apply danger variant styling", () => {
      const { container } = render(<Btn variant="danger">Danger</Btn>);
      const button = container.firstChild as HTMLElement;
      expect(button.className).toContain("text-red-600");
      expect(button.className).toContain("border-red-200");
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

    it("should highlight active tab", () => {
      const { container } = render(
        <Tabs tabs={tabs} active="Tab 2" onChange={() => {}} />
      );

      const buttons = container.querySelectorAll("button");
      const activeButton = Array.from(buttons).find(
        (b) => b.textContent === "Tab 2"
      );
      expect(activeButton?.className).toContain("border-blue-600");
      expect(activeButton?.className).toContain("text-blue-700");
    });

    it("should call onChange with clicked tab", () => {
      const handleChange = vi.fn();
      render(<Tabs tabs={tabs} active="Tab 1" onChange={handleChange} />);

      screen.getByText("Tab 2").click();
      expect(handleChange).toHaveBeenCalledWith("Tab 2");
    });
  });
});
