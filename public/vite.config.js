import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [svelte(), tailwindcss()],

  publicDir: false,

  server: {
    port: 5173,
    strictPort: true
  },

  build: {
    target: "es2020",
    minify: "esbuild",
    cssMinify: true
  }
});
