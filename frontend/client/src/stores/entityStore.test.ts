import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useEntityUIStore, type Entity } from "./entityStore";

const mockEntity: Entity = {
  id: "cap-001",
  name: "Real-Time Analytics",
  type: "Capability",
  confidence: 0.95,
  description: "Process data in real-time",
  properties: { domain: "Analytics" },
  createdAt: "2024-01-01T00:00:00Z",
};

describe("useEntityUIStore", () => {
  beforeEach(() => {
    // Reset store state
    const { result } = renderHook(() => useEntityUIStore());
    act(() => result.current.clearFilters());
    act(() => result.current.selectEntity(null));
  });

  describe("entity selection", () => {
    it("should select an entity", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.selectEntity(mockEntity));

      expect(result.current.selectedEntity).toEqual(mockEntity);
    });

    it("should clear entity selection", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.selectEntity(mockEntity));
      act(() => result.current.selectEntity(null));

      expect(result.current.selectedEntity).toBeNull();
    });

    it("should switch between entities", () => {
      const { result } = renderHook(() => useEntityUIStore());

      const entity1 = { ...mockEntity, id: "cap-001", name: "Entity 1" };
      const entity2 = { ...mockEntity, id: "cap-002", name: "Entity 2" };

      act(() => result.current.selectEntity(entity1));
      expect(result.current.selectedEntity?.name).toBe("Entity 1");

      act(() => result.current.selectEntity(entity2));
      expect(result.current.selectedEntity?.name).toBe("Entity 2");
    });
  });

  describe("search query", () => {
    it("should set search query", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.setSearchQuery("analytics"));

      expect(result.current.searchQuery).toBe("analytics");
    });

    it("should clear search query", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.setSearchQuery("test"));
      act(() => result.current.setSearchQuery(""));

      expect(result.current.searchQuery).toBe("");
    });

    it("should update search query multiple times", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.setSearchQuery("first"));
      act(() => result.current.setSearchQuery("second"));
      act(() => result.current.setSearchQuery("third"));

      expect(result.current.searchQuery).toBe("third");
    });
  });

  describe("type filter", () => {
    it("should set selected type", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.setSelectedType("Capability"));

      expect(result.current.selectedType).toBe("Capability");
    });

    it("should clear type filter", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.setSelectedType("UseCase"));
      act(() => result.current.setSelectedType(null));

      expect(result.current.selectedType).toBeNull();
    });

    it("should support all entity types", () => {
      const { result } = renderHook(() => useEntityUIStore());
      const types = ["Capability", "UseCase", "Persona", "ValueDriver", "KPI"];

      types.forEach((type) => {
        act(() => result.current.setSelectedType(type));
        expect(result.current.selectedType).toBe(type);
      });
    });
  });

  describe("clearFilters", () => {
    it("should clear all filters", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => {
        result.current.setSearchQuery("analytics");
        result.current.setSelectedType("Capability");
        result.current.selectEntity(mockEntity);
      });

      act(() => result.current.clearFilters());

      expect(result.current.searchQuery).toBe("");
      expect(result.current.selectedType).toBeNull();
    });

    it("should not clear selected entity when clearing filters", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => result.current.selectEntity(mockEntity));
      act(() => result.current.setSearchQuery("test"));
      act(() => result.current.clearFilters());

      // Entity selection should persist
      expect(result.current.selectedEntity).toEqual(mockEntity);
      // But filters should be cleared
      expect(result.current.searchQuery).toBe("");
    });

    it("should handle clearing when already empty", () => {
      const { result } = renderHook(() => useEntityUIStore());

      // Should not throw when clearing empty state
      act(() => result.current.clearFilters());

      expect(result.current.searchQuery).toBe("");
      expect(result.current.selectedType).toBeNull();
    });
  });

  describe("combined state", () => {
    it("should maintain independent state properties", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => {
        result.current.selectEntity(mockEntity);
        result.current.setSearchQuery("analytics");
        result.current.setSelectedType("Capability");
      });

      expect(result.current.selectedEntity).toEqual(mockEntity);
      expect(result.current.searchQuery).toBe("analytics");
      expect(result.current.selectedType).toBe("Capability");
    });

    it("should reset to initial state", () => {
      const { result } = renderHook(() => useEntityUIStore());

      act(() => {
        result.current.selectEntity(mockEntity);
        result.current.setSearchQuery("query");
        result.current.setSelectedType("UseCase");
      });

      // Simulate fresh store access
      const { result: freshResult } = renderHook(() => useEntityUIStore());
      
      // Zustand stores are singletons, so state persists
      // This test documents that behavior
      expect(freshResult.current.searchQuery).toBe("query");
      
      // Clean up
      act(() => freshResult.current.clearFilters());
      act(() => freshResult.current.selectEntity(null));
    });
  });
});
