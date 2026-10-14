import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Test runner configuration. The tsconfig has `jsx: "preserve"` because
// Next compiles JSX itself; here esbuild must do it, hence the override.
export default defineConfig({
  esbuild: { jsx: "automatic" },
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
    restoreMocks: true,
  },
});
