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
    "fabric-contracts/no-raw-tenant-query": "off",
    "fabric-contracts/no-explicit-db-connect": "off",
    "fabric-contracts/no-inline-middleware": "off",
    "fabric-contracts/no-inline-tool-definition": "off",
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
