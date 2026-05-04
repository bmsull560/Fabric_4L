import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  formatDate,
  formatRelativeTime,
  formatCurrency,
  formatCompactCurrency,
  formatDistanceToNow,
  truncateString,
} from './formatters';

describe('formatDate', () => {
  it('returns formatted date for valid ISO string', () => {
    // Use a fixed date to avoid locale/timezone issues in CI
    const result = formatDate('2024-06-15T00:00:00.000Z');
    expect(result).toMatch(/Jun\s+\d+,\s+2024/);
  });

  it('returns fallback for undefined input', () => {
    expect(formatDate(undefined)).toBe('—');
  });

  it('returns custom fallback when provided', () => {
    expect(formatDate(undefined, 'N/A')).toBe('N/A');
  });

  it('returns fallback for empty string', () => {
    expect(formatDate('')).toBe('—');
  });
});

describe('formatRelativeTime', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns "just now" for dates within the last minute', () => {
    vi.useFakeTimers();
    const now = new Date('2024-01-01T12:00:00.000Z');
    vi.setSystemTime(now);
    const thirtySecondsAgo = new Date(now.getTime() - 30_000).toISOString();
    expect(formatRelativeTime(thirtySecondsAgo)).toBe('just now');
  });

  it('returns minutes ago for dates within the last hour', () => {
    vi.useFakeTimers();
    const now = new Date('2024-01-01T12:00:00.000Z');
    vi.setSystemTime(now);
    const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000).toISOString();
    expect(formatRelativeTime(tenMinutesAgo)).toBe('10m ago');
  });

  it('returns hours ago for dates within the last day', () => {
    vi.useFakeTimers();
    const now = new Date('2024-01-01T12:00:00.000Z');
    vi.setSystemTime(now);
    const threeHoursAgo = new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(threeHoursAgo)).toBe('3h ago');
  });

  it('returns days ago for dates within the last week', () => {
    vi.useFakeTimers();
    const now = new Date('2024-01-07T12:00:00.000Z');
    vi.setSystemTime(now);
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(threeDaysAgo)).toBe('3d ago');
  });

  it('returns formatted date for dates older than 7 days', () => {
    vi.useFakeTimers();
    const now = new Date('2024-01-30T12:00:00.000Z');
    vi.setSystemTime(now);
    const oldDate = '2024-01-01T00:00:00.000Z';
    const result = formatRelativeTime(oldDate);
    expect(result).toMatch(/Jan\s+\d+,\s+2024/);
  });
});

describe('formatCurrency', () => {
  it('formats a number as compact USD currency', () => {
    const result = formatCurrency(1_500_000);
    expect(result).toMatch(/\$1\.5M|\$1,500,000/);
  });

  it('returns fallback for undefined', () => {
    expect(formatCurrency(undefined)).toBe('—');
  });

  it('returns fallback for null', () => {
    // @ts-expect-error testing null at runtime
    expect(formatCurrency(null)).toBe('—');
  });

  it('returns custom fallback when provided', () => {
    expect(formatCurrency(undefined, 'N/A')).toBe('N/A');
  });

  it('formats zero correctly', () => {
    const result = formatCurrency(0);
    expect(result).toMatch(/\$0/);
  });

  it('formats small positive numbers', () => {
    const result = formatCurrency(500);
    expect(result).toMatch(/\$500/);
  });
});

describe('formatCompactCurrency', () => {
  it('formats billions with B suffix', () => {
    expect(formatCompactCurrency(2_500_000_000)).toBe('$2.5B');
  });

  it('formats millions with M suffix', () => {
    expect(formatCompactCurrency(1_200_000)).toBe('$1.2M');
  });

  it('formats thousands with K suffix', () => {
    expect(formatCompactCurrency(850_000)).toBe('$850.0K');
  });

  it('formats numbers under 1000 without suffix', () => {
    expect(formatCompactCurrency(999)).toBe('$999');
  });

  it('formats exactly 1 billion', () => {
    expect(formatCompactCurrency(1_000_000_000)).toBe('$1.0B');
  });

  it('formats exactly 1 million', () => {
    expect(formatCompactCurrency(1_000_000)).toBe('$1.0M');
  });

  it('formats exactly 1 thousand', () => {
    expect(formatCompactCurrency(1_000)).toBe('$1.0K');
  });
});

describe('formatDistanceToNow', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns fallback for undefined', () => {
    expect(formatDistanceToNow(undefined)).toBe('—');
  });

  it('returns custom fallback when provided', () => {
    expect(formatDistanceToNow(undefined, 'N/A')).toBe('N/A');
  });

  it('returns "Today" for dates that are 0 days old', () => {
    vi.useFakeTimers();
    const now = new Date('2024-06-15T12:00:00.000Z');
    vi.setSystemTime(now);
    // Same day, slightly earlier
    const sameDay = new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString();
    expect(formatDistanceToNow(sameDay)).toBe('Today');
  });

  it('returns "Yesterday" for dates that are 1 day old', () => {
    vi.useFakeTimers();
    const now = new Date('2024-06-15T12:00:00.000Z');
    vi.setSystemTime(now);
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    expect(formatDistanceToNow(yesterday)).toBe('Yesterday');
  });

  it('returns "X days ago" for dates within the last week', () => {
    vi.useFakeTimers();
    const now = new Date('2024-06-15T12:00:00.000Z');
    vi.setSystemTime(now);
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatDistanceToNow(threeDaysAgo)).toBe('3 days ago');
  });

  it('returns "X weeks ago" for dates within the last month', () => {
    vi.useFakeTimers();
    const now = new Date('2024-06-15T12:00:00.000Z');
    vi.setSystemTime(now);
    const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000).toISOString();
    expect(formatDistanceToNow(twoWeeksAgo)).toBe('2 weeks ago');
  });

  it('returns formatted date for dates older than 30 days', () => {
    vi.useFakeTimers();
    const now = new Date('2024-06-15T12:00:00.000Z');
    vi.setSystemTime(now);
    const oldDate = '2024-04-01T00:00:00.000Z';
    const result = formatDistanceToNow(oldDate);
    expect(result).toMatch(/Apr\s+\d+,\s+2024/);
  });
});

describe('truncateString', () => {
  it('returns the string unchanged when under max length', () => {
    expect(truncateString('hello', 10)).toBe('hello');
  });

  it('returns the string unchanged when exactly at max length', () => {
    expect(truncateString('hello', 5)).toBe('hello');
  });

  it('truncates and appends ellipsis when over max length', () => {
    expect(truncateString('hello world', 5)).toBe('hello...');
  });

  it('returns "—" for undefined input', () => {
    expect(truncateString(undefined, 10)).toBe('—');
  });

  it('returns empty string for empty input', () => {
    expect(truncateString('', 10)).toBe('');
  });

  it('handles maxLength of 0', () => {
    expect(truncateString('hello', 0)).toBe('...');
  });
});
