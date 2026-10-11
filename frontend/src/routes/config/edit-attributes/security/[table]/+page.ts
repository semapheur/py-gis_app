import type { PageLoad } from "./$types";
import { loadMsgpack } from "#lib/utils/msgpack.js";
import type { AttributeData } from "#lib/utils/types.js";

export const load: PageLoad = ({ params, fetch }) =>
  loadMsgpack<{ data: AttributeData[] }>(fetch, "/api/attribute-data", {
    query: { table: params.table },
  });
