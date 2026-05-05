import { fromUrl, Pool } from "geotiff";

type PixelValues = Float32Array | Uint16Array | Uint8Array | Int16Array;
export type Extent = [number, number, number, number];

export interface BandStretchRequest {
  requestId: string;
  url: string;
  extent: Extent | null;
  sampleSize?: number;
  lowPercentile: number;
  highPercentile: number;
}

export interface BandStretch {
  min: number;
  max: number;
}

export interface BandStretchResult {
  type: "result";
  requestId: string;
  bands: BandStretch[];
  singleBand: boolean;
}

export interface BandStretchError {
  type: "error";
  requestId: string;
  message: string;
}

const pool = new Pool();

function percentile(values: PixelValues, pct: number): number {
  let lo = Infinity;
  let hi = -Infinity;

  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v === 0 || !isFinite(v)) continue;
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }

  if (lo === Infinity || lo === hi) return lo === Infinity ? 0 : lo;

  const bins = 1000;
  const scale = bins / (hi - lo);
  const hist = new Uint32Array(bins);

  let total = 0;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v === 0 || !isFinite(v)) continue;
    const bin = Math.min(bins - 1, Math.floor((v - lo) * scale));
    hist[bin]++;
    total++;
  }

  const target = Math.round((pct / 100) * total);
  let cumulative = 0;
  for (let b = 0; b < bins; b++) {
    cumulative += hist[b];
    if (cumulative >= target) {
      return lo + b / scale;
    }
  }
  return hi;
}

function chooseOverview(
  image: import("geotiff").GeoTIFFImage,
  windowW: number,
  windowH: number,
  sampleSize: number,
): number {
  return 0;
}

self.onmessage = async (event: MessageEvent<BandStretchRequest>) => {
  const {
    requestId,
    url,
    extent,
    sampleSize = 256,
    lowPercentile = 2,
    highPercentile = 98,
  } = event.data;

  try {
    const tiff = await fromUrl(url, { allowFullFile: false });
    const image = await tiff.getImage();

    const imageWidth = image.getWidth();
    const imageHeight = image.getHeight();
    const bandCount = image.getSamplesPerPixel();
    const singleBand = bandCount === 1;

    let window: Extent | undefined;
    if (extent) {
      const origin = image.getOrigin();
      const resolution = image.getResolution();

      const xRes = Math.abs(resolution[0]);
      const yRes = Math.abs(resolution[1]);

      const imgLeft = origin[0];
      const imgTop = origin[1];

      const [minX, minY, maxX, maxY] = extent;

      const col0 = Math.max(0, Math.floor((minX - imgLeft) / xRes));
      const col1 = Math.min(imageWidth, Math.ceil((maxX - imgLeft) / xRes));

      const row0 = Math.max(0, Math.floor((imgTop - maxY) / yRes));
      const row1 = Math.min(imageHeight, Math.ceil((imgTop - minY) / yRes));

      if (col1 > col0 && row1 > row0) {
        window = [col0, row0, col1, row1];
      }
    }

    const windowWidth = window ? window[2] - window[0] : imageWidth;
    const windowHeight = window ? window[3] - window[1] : imageHeight;

    const overviewLevel = chooseOverview(
      image,
      windowWidth,
      windowHeight,
      sampleSize,
    );

    const rasters = await image.readRasters({
      window,
      samples: Array.from({ length: bandCount }, (_, i) => i),
      pool,
      ...(overviewLevel > 0 ? { resampleMethod: "bilinear" } : {}),
      width: Math.min(windowWidth, sampleSize),
      height: Math.min(windowHeight, sampleSize),
    });

    const bands: BandStretch[] = [];
    for (let b = 0; b < bandCount; b++) {
      const data = Array.isArray(rasters) ? rasters[b] : (rasters as any)[b];
      bands.push({
        min: percentile(data, lowPercentile),
        max: percentile(data, highPercentile),
      });
    }

    const result: BandStretchResult = {
      type: "result",
      requestId,
      bands,
      singleBand,
    };
    self.postMessage(result);
  } catch (e) {
    const error: BandStretchError = {
      type: "error",
      requestId,
      message: e instanceof Error ? e.message : String(e),
    };
    self.postMessage(error);
  }
};
