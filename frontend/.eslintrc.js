/**
 * ESLint Configuration for Frontend
 *
 * CONTRACT.md §3.3 - Lint and CI Enforcement Strategy
 * Enforces Fabric 4L canonical contracts through custom ESLint plugin
 */

module.exports = {
  root: true,
  extends: [
    // Standard TypeScript/React rules
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    // Fabric 4L canonical contracts
    "plugin:fabric-contracts/service-frontend",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: [
    "@typescript-eslint",
    "react-refresh",
    "fabric-contracts",
  ],
  rules: {
    // React specific
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],

    // TypeScript
    "@typescript-eslint/no-explicit-any": "off", // Allow gradual migration
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],

    // Fabric Contract overrides for frontend
    // Phase 1: Enable as warnings (migrate to "error" after fixes)
    "fabric-contracts/no-raw-tenant-query": "warn",
    "fabric-contracts/no-explicit-db-connect": "warn",
    "fabric-contracts/no-inline-middleware": "warn",
    "fabric-contracts/no-inline-tool-definition": "warn",
    // Phase 2: Already enforced
    "fabric-contracts/no-imperative-navigation": "error",
    "fabric-contracts/no-url-concatenation": "error",
  },
  ignorePatterns: [
    "dist/**",
    "node_modules/**",
    "**/*.d.ts",
    "**/*.config.ts",
    "**/*.config.js",
  ],
  settings: {
    react: {
      version: "detect",
    },
  },
};
