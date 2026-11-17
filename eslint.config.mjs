import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: [".venv/**", "node_modules/**", ".vercel/**", "data/**"] },
  {
    files: ["**/*.{js,mjs,cjs}"],
    extends: [js.configs.recommended],
  },
  {
    files: ["frontend/**/*.js"],
    languageOptions: { sourceType: "script", globals: globals.browser },
  },
  {
    files: ["**/*.{ts,mts,cts}"],
    extends: [js.configs.recommended, tseslint.configs.recommended],
  },
);
