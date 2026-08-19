import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { mockApiPlugin } from "./vite.mockApi";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react(), ...(env.VITE_USE_MOCKS === "true" ? [mockApiPlugin()] : [])],
    server: {
      port: 5173,
    },
  };
});
