import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      "/api": "http://0.0.0.0:8080",
      "/thumbnails": "http://0.0.0.0:8080",
    },
  },
});
