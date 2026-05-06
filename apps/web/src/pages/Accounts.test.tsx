import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createWrapperWithRouterPath } from "@/test-utils";
import AccountsPage from "./Accounts";

const mockUseAccounts = vi.fn();
const mockUseAccountFilterOptions = vi.fn();
const mockUseAccountSyncStatus = vi.fn();
const mockUseSyncAccounts = vi.fn();
const mockUseRefreshAccount = vi.fn();
const mockUseNavigation = vi.fn();
const mockUseRoutePrefetch = vi.fn();

vi.mock("@/hooks", () => ({
  useAccounts: (...args: unknown[]) => mockUseAccounts(...args),
  useAccount: vi.fn(() => ({ data: null, isLoading: false, error: null })),
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
  useAccountContextStore: vi.fn((selector: (state: { setAccountId: (id: string) => void }) => unknown) =>
    selector({ setAccountId: vi.fn() })
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
});
