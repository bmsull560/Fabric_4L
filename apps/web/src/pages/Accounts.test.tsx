import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createWrapperWithRouterPath } from "@/test-utils";
import AccountsPage from "./Accounts";

const mockUseAccounts = vi.fn();
const mockUseAccount = vi.fn();
const mockUseAccountFilterOptions = vi.fn();
const mockUseAccountSyncStatus = vi.fn();
const mockUseSyncAccounts = vi.fn();
const mockUseRefreshAccount = vi.fn();
const mockUseNavigation = vi.fn();
const mockUseRoutePrefetch = vi.fn();

vi.mock("@/hooks", () => ({
  useAccounts: (...args: unknown[]) => mockUseAccounts(...args),
  useAccount: (...args: unknown[]) => mockUseAccount(...args),
  useAccountFilterOptions: () => mockUseAccountFilterOptions(),
  useAccountSyncStatus: () => mockUseAccountSyncStatus(),
  useSyncAccounts: () => mockUseSyncAccounts(),
  useRefreshAccount: () => mockUseRefreshAccount(),
  useNavigation: () => mockUseNavigation(),
  useRoutePrefetch: () => mockUseRoutePrefetch(),
}));

const mockUseParams = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...(actual as object),
    useParams: () => mockUseParams(),
  };
});

vi.mock("@/stores/accountContextStore", () => ({
  useAccountContextStore: vi.fn((selector: (state: { setSelectedAccountId: (id: string) => void }) => unknown) =>
    selector({ setSelectedAccountId: vi.fn() })
  ),
}));

vi.mock("@/components/workspace/AccountIntakeModal", () => ({
  default: ({ open }: { open: boolean }) => (
    <div data-testid="account-intake-modal">{open ? "open" : "closed"}</div>
  ),
}));

describe("Accounts page empty state action", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseParams.mockReturnValue({});
    mockUseAccount.mockReturnValue({ data: null, isLoading: false, error: null });
    mockUseAccounts.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
      error: null,
    });
    mockUseAccountFilterOptions.mockReturnValue({ industries: [] });
    mockUseAccountSyncStatus.mockReturnValue([]);
    mockUseSyncAccounts.mockReturnValue({ mutate: vi.fn(), isPending: false });
    mockUseRefreshAccount.mockReturnValue({ mutate: vi.fn(), isPending: false });
    mockUseNavigation.mockReturnValue({ navigateTo: vi.fn() });
    mockUseRoutePrefetch.mockReturnValue({ prefetchAccountDetail: vi.fn() });
  });

  it("opens the account intake modal when empty-state Add account is clicked", async () => {
    const user = userEvent.setup();
    const wrapper = createWrapperWithRouterPath("/accounts");

    render(<AccountsPage />, { wrapper });

    expect(screen.getByTestId("account-intake-modal")).toHaveTextContent("closed");

    await user.click(screen.getByRole("button", { name: "Add account" }));

    expect(screen.getByTestId("account-intake-modal")).toHaveTextContent("open");
  });

  it("renders account rows and detail panel when provider data drifts at runtime", async () => {
    const account = {
      id: "acct-synthetic-alpha",
      name: "Acct Synthetic Alpha",
      domain: "synthetic.example",
      provider: "synthetic",
      provider_record_id: "synthetic-1",
      sync_status: "synced",
      created_at: "2026-05-01T00:00:00Z",
      updated_at: "2026-05-01T00:00:00Z",
      opportunities: [],
    };

    mockUseParams.mockReturnValue({ id: account.id });
    mockUseAccounts.mockReturnValue({
      data: { items: [account], total: 1 },
      isLoading: false,
      error: null,
    });
    mockUseAccount.mockReturnValue({ data: account, isLoading: false, error: null });

    const wrapper = createWrapperWithRouterPath(`/accounts/${account.id}`);

    render(<AccountsPage />, { wrapper });

    expect(screen.getAllByText("Acct Synthetic Alpha").length).toBeGreaterThan(0);
    expect(screen.getByText("External CRM")).toBeInTheDocument();
  });
});
