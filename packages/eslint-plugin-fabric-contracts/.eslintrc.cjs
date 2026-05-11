module.exports = {
  root: true,
  env: {
    es2022: true,
    node: true,
    jest: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
  },
  ignorePatterns: ["dist/", "node_modules/"],
  rules: {
    "no-empty": "error",
    "no-unreachable": "error",
  },
};
