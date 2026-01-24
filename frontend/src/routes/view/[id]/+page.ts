import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";
import type { ImageInfo, RadiometricParams } from "$lib/utils/types";

async function fetchJson<T>(
  fetch: typeof globalThis.fetch,
  input: RequestInfo,
  init?: RequestInit,
  message = "Request failed",
): Promise<T> {
  const response = await fetch(input, init);

  if (!response.ok) {
    throw error(response.status, message);
  }

  return response.json() as Promise<T>;
}

export const load: PageLoad = async ({ params, fetch }) => {
  const id = params.id;
  if (!params.id) throw error(400, "Missing image id");

  const postRequest: RequestInit = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  };

  const [confidenceOptions, statusOptions, imageInfoWithoutId] =
    await Promise.all([
      fetchJson(
        fetch,
        "/api/get-attributes/observation_confidence",
        undefined,
        "Failed to fetch observation confidence attributes",
      ),
      fetchJson(
        fetch,
        "/api/get-attributes/equipment_status",
        undefined,
        "Failed to fetch equipment status attributes",
      ),
      fetchJson<Partial<ImageInfo>>(
        fetch,
        "/api/image-info",
        postRequest,
        "Failed to fetch image info",
      ),
    ]);

  const radiometricParams =
    imageInfoWithoutId.image_type === "slc"
      ? await fetchJson<RadiometricParams>(
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

  return { imageInfo, radiometricParams, confidenceOptions, statusOptions };
};
