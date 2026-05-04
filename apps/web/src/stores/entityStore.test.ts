import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useEntityUIStore } from './entityStore';

describe('useEntityUIStore', () => {
  beforeEach(() => {
    const { result } = renderHook(() => useEntityUIStore());
    act(() => result.current.reset());
  });

  describe('initial state', () => {
    it('has empty searchQuery by default', () => {
      const { result } = renderHook(() => useEntityUIStore());
      expect(result.current.searchQuery).toBe('');
    });

    it('has null selectedType by default', () => {
      const { result } = renderHook(() => useEntityUIStore());
      expect(result.current.selectedType).toBeNull();
    });

    it('has null selectedEntityId by default', () => {
      const { result } = renderHook(() => useEntityUIStore());
      expect(result.current.selectedEntityId).toBeNull();
    });
  });

  describe('setSearchQuery', () => {
    it('updates the search query', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => result.current.setSearchQuery('capability'));
      expect(result.current.searchQuery).toBe('capability');
    });

    it('allows setting back to empty string', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => result.current.setSearchQuery('something'));
      act(() => result.current.setSearchQuery(''));
      expect(result.current.searchQuery).toBe('');
    });
  });

  describe('setSelectedType', () => {
    it('sets a valid entity type', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => result.current.setSelectedType('capability'));
      expect(result.current.selectedType).toBe('capability');
    });

    it('accepts all valid entity types', () => {
      const { result } = renderHook(() => useEntityUIStore());
      const types = ['capability', 'usecase', 'persona', 'valuedriver'] as const;
      for (const type of types) {
        act(() => result.current.setSelectedType(type));
        expect(result.current.selectedType).toBe(type);
      }
    });

    it('can be set to null', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => result.current.setSelectedType('persona'));
      act(() => result.current.setSelectedType(null));
      expect(result.current.selectedType).toBeNull();
    });
  });

  describe('setSelectedEntityId', () => {
    it('sets an entity ID', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => result.current.setSelectedEntityId('ent-123'));
      expect(result.current.selectedEntityId).toBe('ent-123');
    });

    it('can be set to null to deselect', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => result.current.setSelectedEntityId('ent-abc'));
      act(() => result.current.setSelectedEntityId(null));
      expect(result.current.selectedEntityId).toBeNull();
    });
  });

  describe('clearFilters', () => {
    it('resets searchQuery, selectedType, and selectedEntityId', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => {
        result.current.setSearchQuery('test');
        result.current.setSelectedType('usecase');
        result.current.setSelectedEntityId('ent-1');
      });
      act(() => result.current.clearFilters());
      expect(result.current.searchQuery).toBe('');
      expect(result.current.selectedType).toBeNull();
      expect(result.current.selectedEntityId).toBeNull();
    });
  });

  describe('reset', () => {
    it('resets all fields to defaults', () => {
      const { result } = renderHook(() => useEntityUIStore());
      act(() => {
        result.current.setSearchQuery('search');
        result.current.setSelectedType('capability');
        result.current.setSelectedEntityId('ent-999');
      });
      act(() => result.current.reset());
      expect(result.current.searchQuery).toBe('');
      expect(result.current.selectedType).toBeNull();
      expect(result.current.selectedEntityId).toBeNull();
    });
  });
});
