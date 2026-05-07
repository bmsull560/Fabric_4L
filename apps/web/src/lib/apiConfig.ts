/**
 * API Configuration
 * 
 * Centralized API endpoint configuration for SSE and direct API access.
 * These values mirror the configuration in api/client.ts
 */

export const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

// Layer prefixes
export const L1_PREFIX = import.meta.env.VITE_L1_PREFIX || '/ingest';
export const L2_PREFIX = import.meta.env.VITE_L2_PREFIX || '/extract';
export const L3_PREFIX = import.meta.env.VITE_L3_PREFIX || '/graph';
export const L4_PREFIX = import.meta.env.VITE_L4_PREFIX || '/agents';
export const L5_PREFIX = import.meta.env.VITE_L5_PREFIX || '/truths';
export const L6_PREFIX = import.meta.env.VITE_L6_PREFIX || '/benchmarks';

// Special prefixes
export const L4_ANALYSIS_PREFIX = '/v1';

// Re-export layer prefixes for consistency
export const LAYER_PREFIXES = {
  l1: L1_PREFIX,
  l2: L2_PREFIX,
  l3: L3_PREFIX,
  l4: L4_PREFIX,
  l5: L5_PREFIX,
  l6: L6_PREFIX,
} as const;
