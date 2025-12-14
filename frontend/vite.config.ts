import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import glsl from "vite-plugin-glsl";

export default defineConfig({
  plugins: [sveltekit(), glsl()],
  server: {
    proxy: {
      "/api": "http://0.0.0.0:8080",
      "/thumbnails": "http://0.0.0.0:8080",
    },
  },
});
