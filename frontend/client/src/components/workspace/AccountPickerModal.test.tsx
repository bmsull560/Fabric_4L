import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AccountPickerModal from "./AccountPickerModal";
import type { Account, AccountListResponse } from "@/hooks/useAccounts";

const mockNavigate = vi.fn();
const mockSetSelectedAccountId = vi.fn();

// Polyfill scrollIntoView for cmdk in jsdom
Element.prototype.scrollIntoView = vi.fn();

vi.mock("wouter", async () => {
  const actual = await vi.importActual("wouter");
  return {
    ...actual as object,
    useLocation: () => ["/hypothesis", mockNavigate],
  };
});

vi.mock("@/hooks", async () => {
  const actual = await vi.importActual("@/hooks");
  return {
    ...actual as object,
    useAccounts: vi.fn(),
  };
});

vi.mock("@/stores/accountContextStore", () => ({
  useAccountContextStore: (selector: (state: { setSelectedAccountId: typeof mockSetSelectedAccountId }) => unknown) =>
    selector({ setSelectedAccountId: mockSetSelectedAccountId }),
}));

import { useAccounts } from "@/hooks";

const mockUseAccounts = useAccounts as unknown as ReturnType<typeof vi.fn>;

const sampleAccount: Account = {
  id: "acc-001",
  name: "Acme Corp",
  domain: "acme.com",
  provider: "salesforce",
  provider_record_id: "001",
  sync_status: "synced",
  industry: "Technology",
  segment: "Enterprise",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const sampleResponse: AccountListResponse = {
  items: [sampleAccount],
  total: 1,
  page: 1,
  page_size: 50,
  has_more: false,
};

describe("AccountPickerModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton when accounts are loading", () => {
    mockUseAccounts.mockReturnValue({ data: null, isLoading: true, error: null });
    render(<AccountPickerModal workspace="intelligence" tab="signals" />);

    expect(screen.getByText("Select an Account")).toBeInTheDocument();
    expect(screen.getAllByRole("generic").some(el => el.className.includes("animate-pulse"))).toBe(true);
  });

  it("renders accounts and navigates on selection", async () => {
    const user = userEvent.setup();
    mockUseAccounts.mockReturnValue({ data: sampleResponse, isLoading: false, error: null });
    render(<AccountPickerModal workspace="intelligence" tab="signals" />);

    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText(/acme.com/)).toBeInTheDocument();

    const item = screen.getByText("Acme Corp").closest("[cmdk-item]");
    if (item) await user.click(item);

    expect(mockSetSelectedAccountId).toHaveBeenCalledWith("acc-001");
    expect(mockNavigate).toHaveBeenCalledWith("/accounts/acc-001/intelligence/signals");
  });

  it("shows error state when accounts fail to load", () => {
    mockUseAccounts.mockReturnValue({
      data: null,
      isLoading: false,
      error: { message: "Network error" },
    });
    render(<AccountPickerModal workspace="studio" />);

    expect(screen.getByText("Failed to load accounts.")).toBeInTheDocument();
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("navigates to /accounts when Manage Accounts is clicked", async () => {
    const user = userEvent.setup();
    mockUseAccounts.mockReturnValue({ data: sampleResponse, isLoading: false, error: null });
    render(<AccountPickerModal workspace="intelligence" />);

    await user.click(screen.getByRole("button", { name: "Manage Accounts" }));
    expect(mockNavigate).toHaveBeenCalledWith("/accounts");
  });
});
