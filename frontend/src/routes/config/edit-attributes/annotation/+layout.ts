import type { LayoutLoad } from "./$types";
import { loadAttributeTables } from "#lib/utils/fetch/attributes.js";

export const load: LayoutLoad = async ({ fetch }) =>
  loadAttributeTables(fetch, "annotation");
