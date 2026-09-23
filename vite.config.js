import { defineConfig } from "vite";

export default defineConfig({
  root: "src/frontend",
  publicDir: "../../public",
  build: {
    outDir: "../../dist",
    emptyOutDir: false,
  },
});
