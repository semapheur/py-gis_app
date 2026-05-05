import { fromUrl, GeoTIFFImage } from "geotiff";

interface BandStats {
  min: number;
  max: number;
}

export async function getCogOverview(url: string) {
  const tiff = await fromUrl(url);
  const imageCount = await tiff.getImageCount();
  const overview = await tiff.getImage(imageCount - 1);
  return overview;
}

export async function getCogStats(
  image: GeoTIFFImage,
  nodata = 0,
): Promise<BandStats[]> {
  const samplesPerPixel = image.getSamplesPerPixel();
  const embeddedStats: BandStats[] = [];

  for (let band = 0; band < samplesPerPixel; band++) {
    const meta = image.getGDALMetadata(band) ?? image.getGDALMetadata();
    if (meta?.STATISTICS_MINIMUM && meta?.STATISTICS_MAXIMUM) {
      embeddedStats.push({
        min: parseFloat(meta.STATISTICS_MINIMUM),
        max: parseFloat(meta.STATISTICS_MAXIMUM),
      });
    }
  }

  if (embeddedStats.length === samplesPerPixel) {
    return embeddedStats;
  }

  console.debug("[stretch] Computing stats from overview pixels");
  const data = await image.readRasters();
  const bandData = Array.isArray(data) ? data : [data];

  return bandData.map((band) => {
    // Filter out nodata and sort the TypedArray directly
    const validPixels = (band as any).filter(
      (v: number) => v !== nodata && !isNaN(v),
    );
    validPixels.sort();

    return {
      min: validPixels[Math.floor(0.02 * (validPixels.length - 1))] || 0,
      max: validPixels[Math.floor(0.98 * (validPixels.length - 1))] || 255,
    };
  });
}

export function buildStretchStyle(stats: BandStats[]): Record<string, unknown> {
  const [r, g, b] = stats.length >= 3 ? stats : [stats[0], stats[0], stats[0]]; // grayscale fallback

  return {
    color: [
      "array",
      ["clamp", ["/", ["-", ["band", 1], r.min], r.max - r.min], 0, 1],
      ["clamp", ["/", ["-", ["band", 2], g.min], g.max - g.min], 0, 1],
      ["clamp", ["/", ["-", ["band", 3], b.min], b.max - b.min], 0, 1],
      1,
    ],
  };
}
