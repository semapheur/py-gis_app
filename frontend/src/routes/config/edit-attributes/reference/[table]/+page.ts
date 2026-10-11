import type { PageLoad } from "./$types";
import { loadAttributeData } from "#lib/utils/fetch/attributes.js";

export const load: PageLoad = ({ params, fetch }) =>
  loadAttributeData(fetch, params.table);
