import type { PageLoad } from "./$types";
import type { AreaInfo } from "#lib/contexts/area_editor.svelte.js";
import { loadMsgpack } from "#lib/utils/msgpack.js";

export const prerender = false;

export const load: PageLoad = async ({ params, fetch }) =>
  loadMsgpack<AreaInfo>(fetch, "/api/get-area", {
    query: { id: params.id },
  });
