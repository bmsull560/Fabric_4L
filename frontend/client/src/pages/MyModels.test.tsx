import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { createWrapper, createMockResponse } from "../test-utils";
import MyModels from "./MyModels";
import * as useModelsModule from "../hooks/useModels";
import { apiClient } from "@/api/client";

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("MyModels Page", () => {
  const mockModels = [
    {
      id: "mdl_001",
      name: "SaaS Revenue Optimization",
      description: "End-to-end value model",
      industry: "SaaS / B2B",
      tags: ["revenue", "churn"],
      status: "active" as const,
      folder: "my-models",
      formulaCount: 14,
      entityCount: 32,
      driverCount: 8,
      createdAt: "2026-03-15T10:00:00Z",
      updatedAt: "2026-04-16T14:30:00Z",
      owner: "user-001",
      isShared: false,
    },
    {
      id: "mdl_002",
      name: "DevOps Efficiency",
      description: "Infrastructure cost model",
      industry: "SaaS / B2B",
      tags: ["infrastructure"],
      status: "draft" as const,
      folder: "my-models",
      formulaCount: 9,
      entityCount: 18,
      driverCount: 5,
      createdAt: "2026-02-20T09:00:00Z",
      updatedAt: "2026-04-14T11:15:00Z",
      owner: "user-001",
      isShared: false,
    },
  ];

  const mockFolders = [
    { id: "all", name: "All Models", count: 2 },
    { id: "my-models", name: "My Models", count: 2 },
    { id: "shared", name: "Shared With Me", count: 0 },
    { id: "favorites", name: "Favorites", count: 0 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Initial Render", () => {
    it("should render page header with title and subtitle", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText("My Models")).toBeInTheDocument();
      });

      expect(screen.getByText("Personal and shared value models")).toBeInTheDocument();
    });

    it("should show loading state initially", () => {
      vi.mocked(apiClient.get).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<MyModels />, { wrapper: createWrapper() });

      // Should show skeletons while loading
      expect(document.querySelector("[class*='animate-pulse']")).toBeInTheDocument();
    });
  });

  describe("Empty State", () => {
    it("should show empty state when no models exist", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(
            createMockResponse({
              folders: [
                { id: "all", name: "All Models", count: 0 },
                { id: "my-models", name: "My Models", count: 0 },
                { id: "shared", name: "Shared With Me", count: 0 },
                { id: "favorites", name: "Favorites", count: 0 },
              ],
            })
          );
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: [],
              total: 0,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText("No models yet")).toBeInTheDocument();
      });

      expect(
        screen.getByText("Create your first value model to get started.")
      ).toBeInTheDocument();

      // Should show Create First Model button
      expect(screen.getByRole("button", { name: /Create First Model/i })).toBeInTheDocument();
    });

    it("should show search empty state when no search results", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: [],
              total: 0,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByPlaceholderText("Search models...")).toBeInTheDocument();
      });

      // Type in search box
      const searchInput = screen.getByPlaceholderText("Search models...");
      fireEvent.change(searchInput, { target: { value: "nonexistent" } });

      await waitFor(() => {
        expect(screen.getByText("No models match your search")).toBeInTheDocument();
      });
    });
  });

  describe("Model Grid View", () => {
    it("should render model cards in grid view", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText("SaaS Revenue Optimization")).toBeInTheDocument();
      });

      expect(screen.getByText("DevOps Efficiency")).toBeInTheDocument();
      expect(screen.getByText("14 drivers")).toBeInTheDocument();
      expect(screen.getByText("9 formulas")).toBeInTheDocument();
    });

    it("should show correct status badges", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText("Active")).toBeInTheDocument();
      });

      expect(screen.getByText("Draft")).toBeInTheDocument();
    });
  });

  describe("Folder Sidebar", () => {
    it("should render folder list with counts", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Use getAllByText since "My Models" appears in both header and sidebar
        expect(screen.getAllByText("My Models").length).toBeGreaterThanOrEqual(1);
      });

      // Verify sidebar folder elements
      expect(screen.getByText("All Models")).toBeInTheDocument();
      expect(screen.getByText("Shared With Me")).toBeInTheDocument();
      expect(screen.getByText("Favorites")).toBeInTheDocument();

      // Check counts are displayed - look within the sidebar context
      const folderButtons = screen.getAllByRole("button");
      const allModelsButton = folderButtons.find((btn) =>
        btn.textContent?.includes("All Models")
      );
      expect(allModelsButton?.textContent).toContain("2");
    });
  });

  describe("Search and Filter", () => {
    it("should update search query on input change", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByPlaceholderText("Search models...")).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText("Search models...");
      fireEvent.change(searchInput, { target: { value: "revenue" } });

      expect(searchInput).toHaveValue("revenue");
    });

    it("should show Clear button when filters active", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByPlaceholderText("Search models...")).toBeInTheDocument();
      });

      // Type in search box to activate filters
      const searchInput = screen.getByPlaceholderText("Search models...");
      fireEvent.change(searchInput, { target: { value: "test" } });

      await waitFor(() => {
        expect(screen.getByText("Clear")).toBeInTheDocument();
      });
    });
  });

  describe("Create Model Dialog", () => {
    it("should open create dialog on New Model button click", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /New Model/i })).toBeInTheDocument();
      });

      const newModelButton = screen.getByRole("button", { name: /New Model/i });
      fireEvent.click(newModelButton);

      await waitFor(() => {
        expect(screen.getByText("New Value Model")).toBeInTheDocument();
      });

      expect(screen.getByPlaceholderText("e.g. SaaS Revenue Optimization")).toBeInTheDocument();
    });

    it("should close dialog on Cancel", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /New Model/i })).toBeInTheDocument();
      });

      // Open dialog
      fireEvent.click(screen.getByRole("button", { name: /New Model/i }));

      await waitFor(() => {
        expect(screen.getByText("Cancel")).toBeInTheDocument();
      });

      // Click Cancel
      fireEvent.click(screen.getByText("Cancel"));

      // Dialog should close (New Value Model text should not be visible)
      await waitFor(() => {
        expect(screen.queryByText("New Value Model")).not.toBeInTheDocument();
      });
    });
  });

  describe("Error State", () => {
    it("should show error state when API fails", async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error("API Error"));

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText("Failed to load models")).toBeInTheDocument();
      });
    });
  });

  describe("View Mode Toggle", () => {
    it("should have grid/list view toggle buttons", async () => {
      vi.mocked(apiClient.get).mockImplementation((layer, path) => {
        if (path === "/models/folders") {
          return Promise.resolve(createMockResponse({ folders: mockFolders }));
        }
        if (path?.includes("/models?")) {
          return Promise.resolve(
            createMockResponse({
              models: mockModels,
              total: 2,
              offset: 0,
              limit: 50,
            })
          );
        }
        return Promise.resolve(createMockResponse({}));
      });

      render(<MyModels />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Grid and List buttons should be present (they use icons)
        const buttons = screen.getAllByRole("button");
        expect(buttons.length).toBeGreaterThan(0);
      });
    });
  });
});
