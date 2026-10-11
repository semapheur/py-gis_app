import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";
import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "#lib/utils/types.js";
import type { AnnotationInfo } from "#lib/contexts/annotate.svelte.js";
import type { AreaInfo } from "#lib/contexts/area_editor.svelte.js";
import {
  equipmentAttributeTables,
  type EquipmentAttributeName,
} from "#lib/schemas/equipment_annotation.js";
import { loadMsgpack } from "#lib/utils/msgpack.js";

export const prerender = false;

type AttributeOptions = { options: SelectOption[] };

export const load: PageLoad = async ({ params, fetch }) => {
  const id = params.id;
  if (!params.id) throw error(400, "Missing image id");

  const [attributeEntries, imageInfoWithoutId, annotations, areas] =
    await Promise.all([
      Promise.all(
        Object.entries(equipmentAttributeTables).map(
          async ([name, table]) =>
            [
              name,
              await loadMsgpack(fetch, "/api/get-attributes", {
                query: { table },
              }),
            ] as const,
        ),
      ),
      loadMsgpack<Partial<ImageInfo>>(fetch, "/api/image-info", {
        query: { id },
      }),
      loadMsgpack<AnnotationInfo[]>(fetch, "/api/get-annotations-by-image", {
        query: { id },
      }),
      loadMsgpack<AreaInfo[]>(fetch, "/api/get-areas-by-image", {
        query: { id },
      }),
    ]);

  const attributes = Object.fromEntries(attributeEntries) as Record<
    EquipmentAttributeName,
    AttributeOptions
  >;

  const radiometricParams =
    imageInfoWithoutId.image_type === "slc"
      ? await loadMsgpack<RadiometricParams>(fetch, "/api/radiometric-params", {
          method: "POST",
          body: { id },
        })
      : null;

  return {
    imageInfo: {
      id,
      ...imageInfoWithoutId,
    } as ImageInfo,
    radiometricParams,
    ...attributes,
    annotations,
    areas,
  };
};
