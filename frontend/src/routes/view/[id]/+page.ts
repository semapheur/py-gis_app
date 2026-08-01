import { error } from "@sveltejs/kit";
import { encode, decode } from "@msgpack/msgpack";
import type { PageLoad } from "./$types";
import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "$lib/utils/types";
import type { AnnotationInfo } from "$lib/contexts/annotate.svelte";
import type { AreaInfo } from "$lib/contexts/area_editor.svelte";

export const prerender = false;

const ATTRIBUTE_FIELDS = {
  confidenceOptions: "equipment_confidence",
  statusOptions: "equipment_status",
  visibilityOptions: "equipment_visibility",
  configurationOptions: "equipment_configuration",
  modificationOptions: "equipment_modification",
  camoflageOptions: "equipment_camoflage",
} as const;

type AttributeOptionsName = keyof typeof ATTRIBUTE_FIELDS;

async function fetchMsgPack<T>(
  fetch: typeof globalThis.fetch,
  input: RequestInfo,
  init?: RequestInit,
  message = "Request failed",
): Promise<T> {
  const response = await fetch(input, init);

  if (!response.ok) {
    throw error(response.status, message);
  }

  const buffer = await response.arrayBuffer();
  return decode(buffer) as T;
}

export const load: PageLoad = async ({ params, fetch }) => {
  const id = params.id;
  if (!params.id) throw error(400, "Missing image id");

  const postRequest: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/msgpack" },
    body: encode({ id }),
  };

  const [attributeResults, imageInfoWithoutId, annotations] = await Promise.all(
    [
      Promise.all(
        Object.values(ATTRIBUTE_FIELDS).map((table) =>
          fetchMsgPack(
            fetch,
            `/api/get-attributes/${table}`,
            undefined,
            `Failed to fetch ${table.replace("_", " ")} attributes`,
          ),
        ),
      ),
      fetchMsgPack<Partial<ImageInfo>>(
        fetch,
        "/api/image-info",
        postRequest,
        "Failed to fetch image info",
      ),
      fetchMsgPack<AnnotationInfo[]>(
        fetch,
        `/api/get-annotations-by-image/${id}`,
        undefined,
        `Failed to fetch annotations for ${id}`,
      ),
      fetchMsgPack<AreaInfo[]>(
        fetch,
        `/api/get-areas-by-image/${id}`,
        undefined,
        `Failed to fetch areas for ${id}`,
      ),
    ],
  );

  const attributes = Object.fromEntries(
    Object.keys(ATTRIBUTE_FIELDS).map((name, i) => [name, attributeResults[i]]),
  ) as Record<AttributeOptionsName, { options: SelectOption[] }>;

  const radiometricParams =
    imageInfoWithoutId.image_type === "slc"
      ? await fetchMsgPack<RadiometricParams>(
          fetch,
          "/api/radiometric-params",
          postRequest,
          "Failed to fetch radiometric parameters",
        )
      : null;

  const imageInfo = {
    id,
    ...imageInfoWithoutId,
  } as ImageInfo;

  return {
    imageInfo,
    radiometricParams,
    ...attributes,
    annotations,
  };
};
