import { TuskDrift } from "@use-tusk/drift-node-sdk";

TuskDrift.initialize({
  apiKey: process.env.TUSK_DRIFT_API_KEY,
  env: process.env.NODE_ENV ?? "development",
});

export { TuskDrift };
