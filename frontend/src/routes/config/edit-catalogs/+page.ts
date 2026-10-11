import type { PageLoad } from "./$types";
import { loadMsgpack } from "#lib/utils/msgpack.js";

export const load: PageLoad = async ({ fetch }) =>
  loadMsgpack<{ catalogs: [] }>(fetch, "/api/get-catalogs-edit");
