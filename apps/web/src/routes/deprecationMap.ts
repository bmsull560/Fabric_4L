export const aliasNamespaceDeprecationMap = {
  trust: "/governance",
  evidence: "/governance",
  admin: "/settings",
  discover: "/context",
  library: "/context",
  model: "/studio",
  deliver: "/deliverables",
} as const;

export type AliasNamespace = keyof typeof aliasNamespaceDeprecationMap;
