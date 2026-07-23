import { error } from "@sveltejs/kit";
import { encode, decode } from "@msgpack/msgpack";
import type { PageLoad } from "./$types";
import type { ImageInfo, RadiometricParams } from "$lib/utils/types";
import type { AnnotationInfo } from "$lib/contexts/annotate.svelte";

export const prerender = false;

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

  const [
    schemaOptions,
    confidenceOptions,
    statusOptions,
    configurationOptions,
    modificationOptions,
    visibilityOptions,
    imageInfoWithoutId,
    annotations,
  ] = await Promise.all([
    fetchMsgPack(
      fetch,
      "/api/schema-options",
      undefined,
      "Failed to fetch schema options",
    ),
    fetchMsgPack(
      fetch,
      "/api/get-attributes/observation_confidence",
      undefined,
      "Failed to fetch observation confidence attributes",
    ),
    fetchMsgPack(
      fetch,
      "/api/get-attributes/equipment_status",
      undefined,
      "Failed to fetch equipment status attributes",
    ),
    fetchMsgPack(
      fetch,
      "/api/get-attributes/equipment_configuration",
      undefined,
      "Failed to fetch equipment configuration attributes",
    ),
    fetchMsgPack(
      fetch,
      "/api/get-attributes/equipment_modification",
      undefined,
      "Failed to fetch equipment modification attributes",
    ),
    fetchMsgPack(
      fetch,
      "/api/get-attributes/equipment_visibility",
      undefined,
      "Failed to fetch equipment visibility attributes",
    ),
    fetchMsgPack<Partial<ImageInfo>>(
      fetch,
      "/api/image-info",
      postRequest,
      "Failed to fetch image info",
    ),
    fetchMsgPack<AnnotationInfo[]>(
      fetch,
      `/api/get-annotations/${id}`,
      undefined,
      `Failed to fetch annotations for ${id}`,
    ),
  ]);

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
    schemaOptions,
    confidenceOptions,
    configurationOptions,
    modificationOptions,
    visibilityOptions,
    statusOptions,
    annotations,
  };
};
