import type { LayoutLoad } from "./$types";
import type { TableNameLabel } from "#lib/utils/types.js";
import { loadMsgpack } from "#lib/utils/msgpack.js";

export const load: LayoutLoad = async ({ fetch }) =>
  loadMsgpack<{ tables: TableNameLabel[] }>(fetch, "/api/attribute-tables", {
    query: { type: "annotation" },
  });
