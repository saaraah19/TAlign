// ESLint 9 "flat" config. `npm run lint` used to fail outright because
// this file did not exist (eslint-config-next was installed but never wired).
// FlatCompat adapts Next's shareable config, which is still published in
// the older format, to ESLint 9's flat format.
import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

const eslintConfig = [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts", "coverage/**", "out/**"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // Test fixtures are deliberately loose about the exact shape of API payloads.
    files: ["**/*.test.{ts,tsx}", "src/test/**"],
    rules: { "@typescript-eslint/no-explicit-any": "off" },
  },
];

export default eslintConfig;
