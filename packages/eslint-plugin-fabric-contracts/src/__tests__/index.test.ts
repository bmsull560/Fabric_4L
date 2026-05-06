import plugin = require("../index");

const expectedRules = [
  "no-tenant-id-parameter",
  "no-req-tenant-access",
  "no-raw-tenant-query",
  "no-explicit-db-connect",
  "no-inline-middleware",
  "no-inline-tool-definition",
  "no-throw-in-tool",
  "no-json-parse-agent-output",
  "no-imperative-navigation",
  "no-url-concatenation",
  "no-private-imports",
  "no-circular-dependencies",
];

describe("eslint-plugin-fabric-contracts", () => {
  it("exports all canonical contract rules", () => {
    expect(plugin.meta).toEqual({
      name: "eslint-plugin-fabric-contracts",
      version: "1.0.0",
    });

    expect(Object.keys(plugin.rules).sort()).toEqual([...expectedRules].sort());
  });

  it("enables all exported rules in the recommended config", () => {
    expect(plugin.configs.recommended.plugins).toEqual(["fabric-contracts"]);

    for (const ruleName of expectedRules) {
      expect(plugin.configs.recommended.rules?.[`fabric-contracts/${ruleName}`]).toBe(
        "error"
      );
    }
  });

  it("provides backend and frontend service-specific rule overrides", () => {
    expect(plugin.configs["service-backend"].rules).toMatchObject({
      "fabric-contracts/no-imperative-navigation": "off",
      "fabric-contracts/no-url-concatenation": "off",
      "fabric-contracts/no-tenant-id-parameter": "error",
    });

    expect(plugin.configs["service-frontend"].rules).toMatchObject({
      "fabric-contracts/no-raw-tenant-query": "off",
      "fabric-contracts/no-explicit-db-connect": "off",
      "fabric-contracts/no-private-imports": "error",
    });
  });
});
