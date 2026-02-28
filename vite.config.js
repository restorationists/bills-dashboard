import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [svelte(), tailwindcss()],

  server: {
    port: 5173,
    strictPort: true
  },

  build: {
    target: "es2020",
    minify: "esbuild",
    cssMinify: true,
    outDir: "../dist",
    emptyOutDir: true
  }
});
