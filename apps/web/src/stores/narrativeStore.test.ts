import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useNarrativeStore, looksLikeUrl, FALLBACK_INDUSTRIES, DEFAULT_INDUSTRY } from './narrativeStore';

// ── looksLikeUrl ──────────────────────────────────────────────────────────────

describe('looksLikeUrl', () => {
  it('returns true for http:// URLs', () => {
    expect(looksLikeUrl('http://example.com')).toBe(true);
  });

  it('returns true for https:// URLs', () => {
    expect(looksLikeUrl('https://example.com/path')).toBe(true);
  });

  it('returns true for bare domain names', () => {
    expect(looksLikeUrl('example.com')).toBe(true);
    expect(looksLikeUrl('my-company.io')).toBe(true);
  });

  it('returns false for plain text', () => {
    expect(looksLikeUrl('just some description')).toBe(false);
  });

  it('returns false for empty string', () => {
    expect(looksLikeUrl('')).toBe(false);
  });

  it('trims whitespace before checking', () => {
    expect(looksLikeUrl('  https://example.com  ')).toBe(true);
    expect(looksLikeUrl('  plain text  ')).toBe(false);
  });

  it('is case-insensitive for the protocol', () => {
    expect(looksLikeUrl('HTTPS://example.com')).toBe(true);
    expect(looksLikeUrl('HTTP://example.com')).toBe(true);
  });
});

// ── useNarrativeStore ─────────────────────────────────────────────────────────

describe('useNarrativeStore', () => {
  beforeEach(() => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => result.current.reset());
  });

  it('has correct initial state', () => {
    const { result } = renderHook(() => useNarrativeStore());
    expect(result.current.prompt).toBe('');
    expect(result.current.outputType).toBe('narrative');
    expect(result.current.industry).toBe(DEFAULT_INDUSTRY);
    expect(result.current.inputMethod).toBe('text');
  });

  it('setPrompt updates prompt', () => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => result.current.setPrompt('My description'));
    expect(result.current.prompt).toBe('My description');
  });

  it('setOutputType updates outputType', () => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => result.current.setOutputType('roi_model'));
    expect(result.current.outputType).toBe('roi_model');
  });

  it('setOutputType can be set to value_template', () => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => result.current.setOutputType('value_template'));
    expect(result.current.outputType).toBe('value_template');
  });

  it('setIndustry updates industry', () => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => result.current.setIndustry('Healthcare'));
    expect(result.current.industry).toBe('Healthcare');
  });

  it('setInputMethod updates inputMethod', () => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => result.current.setInputMethod('import'));
    expect(result.current.inputMethod).toBe('import');

    act(() => result.current.setInputMethod('file'));
    expect(result.current.inputMethod).toBe('file');

    act(() => result.current.setInputMethod('crm'));
    expect(result.current.inputMethod).toBe('crm');
  });

  it('reset returns all fields to defaults', () => {
    const { result } = renderHook(() => useNarrativeStore());
    act(() => {
      result.current.setPrompt('some text');
      result.current.setOutputType('roi_model');
      result.current.setIndustry('Healthcare');
      result.current.setInputMethod('file');
    });
    act(() => result.current.reset());
    expect(result.current.prompt).toBe('');
    expect(result.current.outputType).toBe('narrative');
    expect(result.current.industry).toBe(DEFAULT_INDUSTRY);
    expect(result.current.inputMethod).toBe('text');
  });
});

// ── Constants ─────────────────────────────────────────────────────────────────

describe('narrativeStore constants', () => {
  it('FALLBACK_INDUSTRIES is a non-empty array', () => {
    expect(Array.isArray(FALLBACK_INDUSTRIES)).toBe(true);
    expect(FALLBACK_INDUSTRIES.length).toBeGreaterThan(0);
  });

  it('DEFAULT_INDUSTRY is included in FALLBACK_INDUSTRIES', () => {
    expect(FALLBACK_INDUSTRIES).toContain(DEFAULT_INDUSTRY);
  });
});
