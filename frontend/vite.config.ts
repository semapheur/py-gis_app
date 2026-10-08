import adapter from "@sveltejs/adapter-static";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import glsl from "vite-plugin-glsl";

export default defineConfig({
  plugins: [
    sveltekit({
      compilerOptions: {
        // Force runes mode for the project, except for libraries. Can be removed in svelte 6.
        runes: ({ filename }) =>
          filename.split(/[/\\]/).includes("node_modules") ? undefined : true,
      },
      adapter: adapter({
        fallback: "200.html",
      }),
    }),
    glsl(),
  ],
  server: {
    proxy: {
      "/api": "http://0.0.0.0:8080",
      "/thumbnails": "http://0.0.0.0:8080",
    },
  },
  optimizeDeps: {
    exclude: ["ol"],
  },
});
