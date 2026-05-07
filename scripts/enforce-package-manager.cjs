#!/usr/bin/env node

const ua = process.env.npm_config_user_agent || "";

if (!ua.includes("pnpm")) {
  console.error("❌ This repository uses pnpm. Install dependencies with: pnpm install");
  process.exit(1);
}
