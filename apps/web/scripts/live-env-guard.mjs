#!/usr/bin/env node
/**
 * Fail-closed guard for Fabric 4L live workflow validation commands.
 *
 * Live validation must exercise a real frontend against a real backend. This
 * guard rejects ambiguous command invocations that would otherwise fall back to
 * mocked APIs, missing backend URLs, or non-live Playwright settings.
 */

const mode = process.argv[2] ?? 'test';

const REQUIREMENTS = {
  dev: {
    required: ['VITE_API_BASE_URL', 'VITE_PROXY_L1_URL', 'VITE_PROXY_L2_URL', 'VITE_PROXY_L3_URL', 'VITE_PROXY_L4_URL', 'VITE_PROXY_L5_URL', 'VITE_PROXY_L6_URL'],
    liveMode: false,
    backend: false,
    frontend: false,
  },
  seed: {
    required: ['PLAYWRIGHT_BACKEND_URL'],
    liveMode: false,
    backend: true,
    frontend: false,
  },
  test: {
    required: ['PLAYWRIGHT_LIVE_MODE', 'PLAYWRIGHT_LIVE_FRONTEND_URL', 'PLAYWRIGHT_BACKEND_URL'],
    liveMode: true,
    backend: true,
    frontend: true,
  },
};

const config = REQUIREMENTS[mode];
if (!config) {
  fail(`Unknown live guard mode "${mode}". Expected one of: ${Object.keys(REQUIREMENTS).join(', ')}.`);
}

const errors = [];
for (const name of config.required) {
  const value = process.env[name];
  if (!value || value.trim() === '') {
    errors.push(`${name} is required`);
  }
}

if (config.liveMode && process.env.PLAYWRIGHT_LIVE_MODE !== 'true') {
  errors.push('PLAYWRIGHT_LIVE_MODE must be exactly "true" for live Playwright validation');
}

for (const name of ['VITE_USE_MOCKS', 'VITE_ENABLE_MOCK_FALLBACK', 'MSW', 'MOCKS_ENABLED']) {
  const value = process.env[name];
  if (typeof value === 'string' && /^(1|true|yes|on)$/i.test(value.trim())) {
    errors.push(`${name} must not enable mocks during live validation`);
  }
}

if (config.backend) {
  const backendUrl = process.env.PLAYWRIGHT_BACKEND_URL;
  if (backendUrl && !isHttpUrl(backendUrl)) {
    errors.push('PLAYWRIGHT_BACKEND_URL must be an http(s) URL');
  }
}

if (config.frontend) {
  const frontendUrl = process.env.PLAYWRIGHT_LIVE_FRONTEND_URL;
  if (frontendUrl && !isHttpUrl(frontendUrl)) {
    errors.push('PLAYWRIGHT_LIVE_FRONTEND_URL must be an http(s) URL');
  }
}

if (mode === 'dev') {
  for (const name of config.required) {
    const value = process.env[name];
    if (value && !isHttpUrl(value)) {
      errors.push(`${name} must be an http(s) URL`);
    }
  }
}

if (errors.length > 0) {
  fail(`Live validation environment is not safe to run:\n- ${errors.join('\n- ')}`);
}

console.log(`[live-env-guard] ${mode} environment accepted; mocks disabled and required live URLs present.`);

function isHttpUrl(value) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
