import { defineConfig } from "@playwright/test";

// Runs against the dev server in mock mode -- e2e coverage doesn't wait
// on Yashasvi's backend branch.
export default defineConfig({
  testDir: "./e2e",
  webServer: {
    command: "npm run dev -- --port 4173",
    port: 4173,
    reuseExistingServer: !process.env.CI,
    env: {
      VITE_USE_MOCKS: "true",
    },
  },
  use: {
    baseURL: "http://localhost:4173",
  },
});
