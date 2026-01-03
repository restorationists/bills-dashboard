import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],

  // Your project root already contains the static files
  // (otherwise Vite would look in ./public, i.e. ./public/public)
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
