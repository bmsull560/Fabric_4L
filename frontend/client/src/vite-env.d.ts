/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
  readonly VITE_L1_PREFIX: string;
  readonly VITE_L2_PREFIX: string;
  readonly VITE_L3_PREFIX: string;
  readonly VITE_L4_PREFIX: string;
  readonly VITE_L5_PREFIX: string;
  readonly VITE_L6_PREFIX: string;
  // Add more env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
