import type { PageLoad } from "./$types";
import type { ImageMetadata, RadiometricParams } from "$lib/utils/types";

export const load: PageLoad = async ({ params, fetch }) => {
  const id = params.id;
  const request = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  };

  const imageResult = await fetch("/api/image-info", request);
  if (!imageResult.ok) {
    throw new Error("Failed to fetch image info");
  }

  const image: ImageMetadata = await imageResult.json();

  let radiometricParams: RadiometricParams | null = null;

  if (image.image_type === "slc") {
    const radiometricResult = await fetch("/api/radiometric-params", request);
    if (!radiometricResult.ok) {
      throw new Error("Failed to fetch radiometric parameters");
    }
    radiometricParams = await radiometricResult.json();
  }

  return { image, radiometricParams };
};
