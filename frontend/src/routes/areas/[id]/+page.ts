import { error } from "@sveltejs/kit";
import { encode, decode } from "@msgpack/msgpack";
import type { PageLoad } from "./$types";
import type { AreaInfo } from "$lib/contexts/area_editor.svelte";

export const prerender = false;

export const load: PageLoad = async ({ params, fetch }) => {
  const id = params.id;
  if (!params.id) throw error(400, "Missing image id");

  const response = await fetch("/api/get-area", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: encode({ id }),
  });

  if (!response.ok) {
    throw error(response.status, `Failed to fetch area for id ${id}`);
  }

  const buffer = await response.arrayBuffer();
  const areaInfo = decode(buffer) as AreaInfo;

  return areaInfo;
};
