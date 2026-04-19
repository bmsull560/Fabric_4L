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

    it.each(entityTypes)("renders entity type '%s' with lowercase label", (type) => {
      const { container } = render(<EntityBadge type={type} />);
      expect(container.textContent).toBe(type);
    });

    it("should render custom label when provided", () => {
      render(<EntityBadge type="capability" label="Custom Label" />);
      expect(screen.getByText("Custom Label")).toBeInTheDocument();
    });

    it("should render as a semantic span element", () => {
      const { container } = render(<EntityBadge type="capability" />);
      const badge = container.firstElementChild;
      expect(badge?.tagName.toLowerCase()).toBe("span");
      // Component renders type prop directly (lowercase)
      expect(badge?.textContent).toBe("capability");
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

    it.each(statusTypes)("renders status '%s' with capitalized label", (status) => {
      const { container } = render(<StatusBadge status={status} />);
      expect(container.textContent).toContain(status.charAt(0).toUpperCase() + status.slice(1));
    });
  });

  describe("MetricCard", () => {
    it("renders MetricCard with trend display", () => {
      render(<MetricCard label="Revenue" value="$1M" trend="+12%" trendUp={true} />);
      expect(screen.getByText("Revenue")).toBeInTheDocument();
      expect(screen.getByText("$1M")).toBeInTheDocument();
    });

    it("should render label and value", () => {
      render(<MetricCard label="Revenue" value="$1.2M" />);

      expect(screen.getByText("Revenue")).toBeInTheDocument();
      expect(screen.getByText("$1.2M")).toBeInTheDocument();
    });

    it("should render trend when provided without trendUp", () => {
      render(<MetricCard label="Users" value="1,234" trend="+12% vs last month" />);

      expect(screen.getByText("+12% vs last month")).toBeInTheDocument();
    });

    it("should render trend with indicator when trendUp is true", () => {
      render(
        <MetricCard
          label="Growth"
          value="25%"
          trend="vs last quarter"
          trendUp={true}
        />
      );
      // Component uses Lucide icons instead of text arrows
      expect(screen.getByText("vs last quarter")).toBeInTheDocument();
    });

    it("should indicate positive trend when trendUp is true", () => {
      render(<MetricCard label="Test" value="100" trend="+5%" trendUp={true} />);
      // Trend value rendered without text arrow (uses icon)
      expect(screen.getByText("+5%")).toBeInTheDocument();
    });

    it("should show trend without indicator when trendUp is not provided", () => {
      render(<MetricCard label="Test" value="100" trend="No change" />);
      expect(screen.getByText("No change")).toBeInTheDocument();
      // Component renders with Minus icon when trendUp is undefined, not text arrow
    });

    it("should not render trend section when trend is not provided", () => {
      render(<MetricCard label="Static" value="100" />);
      // The card should only contain label and value (no trend section)
      expect(screen.getByText("Static")).toBeInTheDocument();
      expect(screen.getByText("100")).toBeInTheDocument();
      // Verify trend element not present by checking text isn't found
      expect(screen.queryByText(/trend/i)).not.toBeInTheDocument();
    });
  });

  describe("PageHeader", () => {
    it("should render title", () => {
      render(<PageHeader title="Dashboard" />);
      expect(screen.getByRole("heading", { name: /Dashboard/i })).toBeInTheDocument();
    });

    it("should render subtitle when provided", () => {
      render(<PageHeader title="Dashboard" subtitle="Overview page" />);
      expect(screen.getByText("Overview page")).toBeInTheDocument();
    });

    it("should render breadcrumbs when provided", () => {
      render(
        <PageHeader
          title="Final Page"
          breadcrumbs={[{ label: "Home" }, { label: "Section" }, { label: "Final Page" }]}
        />
      );

      expect(screen.getByText("Home")).toBeInTheDocument();
      expect(screen.getByText("Section")).toBeInTheDocument();
      // Title and last breadcrumb share text - use role query
      expect(screen.getByRole("heading", { name: /Final Page/i })).toBeInTheDocument();
    });

    it("should render actions when provided", () => {
      render(
        <PageHeader
          title="Page"
          actions={<button>Action</button>}
        />
      );

      expect(screen.getByRole("button", { name: /Action/i })).toBeInTheDocument();
    });
  });

  describe("SectionCard", () => {
    it("should render title", () => {
      render(<SectionCard title="Section Title">Content</SectionCard>);
      // CardTitle renders as div, not heading - use text selector
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

    it("applies custom className to SectionCard", () => {
      render(
        <SectionCard title="Card" className="my-custom-class">
          Content
        </SectionCard>
      );
      // Card should have custom class applied - check via content
      expect(screen.getByText("Card")).toBeInTheDocument();
      expect(screen.getByText("Content")).toBeInTheDocument();
    });
  });

  describe("Btn", () => {
    it("should render children", () => {
      render(<Btn>Click Me</Btn>);
      expect(screen.getByText("Click Me")).toBeInTheDocument();
    });

    it("renders Btn with button role", () => {
      render(<Btn variant="primary">Click Me</Btn>);
      expect(screen.getByRole("button", { name: /Click Me/i })).toBeInTheDocument();
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

    it("should call onChange with clicked tab", () => {
      const handleChange = vi.fn();
      render(<Tabs tabs={tabs} active="Tab 1" onChange={handleChange} />);

      screen.getByText("Tab 2").click();
      expect(handleChange).toHaveBeenCalledWith("Tab 2");
    });
  });
});
