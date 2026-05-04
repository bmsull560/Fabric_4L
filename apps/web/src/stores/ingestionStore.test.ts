import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useIngestionUIStore } from './ingestionStore';

describe('useIngestionUIStore', () => {
  beforeEach(() => {
    const { result } = renderHook(() => useIngestionUIStore());
    act(() => result.current.reset());
  });

  describe('initial state', () => {
    it('has empty domainInput by default', () => {
      const { result } = renderHook(() => useIngestionUIStore());
      expect(result.current.domainInput).toBe('');
    });
  });

  describe('setDomainInput', () => {
    it('updates domainInput', () => {
      const { result } = renderHook(() => useIngestionUIStore());
      act(() => result.current.setDomainInput('https://example.com'));
      expect(result.current.domainInput).toBe('https://example.com');
    });

    it('can be set to empty string', () => {
      const { result } = renderHook(() => useIngestionUIStore());
      act(() => result.current.setDomainInput('something.com'));
      act(() => result.current.setDomainInput(''));
      expect(result.current.domainInput).toBe('');
    });

    it('accepts arbitrary text input', () => {
      const { result } = renderHook(() => useIngestionUIStore());
      act(() => result.current.setDomainInput('my.subdomain.example.org/path'));
      expect(result.current.domainInput).toBe('my.subdomain.example.org/path');
    });
  });

  describe('reset', () => {
    it('resets domainInput to empty string', () => {
      const { result } = renderHook(() => useIngestionUIStore());
      act(() => result.current.setDomainInput('https://acme.com'));
      act(() => result.current.reset());
      expect(result.current.domainInput).toBe('');
    });
  });
});
