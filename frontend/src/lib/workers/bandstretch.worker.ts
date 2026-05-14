import { fromUrl, Pool } from "geotiff";

type PixelValues = Float32Array | Uint16Array | Uint8Array | Int16Array;
export type Extent = [number, number, number, number];

export interface BandStretchRequest {
  requestId: string;
  url: string;
  extent: Extent | null;
  sampleSize?: number;
  lowPercentile?: number;
  highPercentile?: number;
  isComplex?: boolean;
}

export interface BandStretch {
  min: number;
  max: number;
  isLog: boolean;
}

export interface BandStretchResult {
  type: "result";
  requestId: string;
  bands: BandStretch[];
  singleBand: boolean;
  isComplex: boolean;
}

export interface BandStretchError {
  type: "error";
  requestId: string;
  message: string;
}

const pool = new Pool();

function computePercentile(
  values: PixelValues,
  percentile: number,
  skipZero: boolean = true,
): number {
  // Find min/max pixel values
  let lo = Infinity;
  let hi = -Infinity;

  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v === 0 && skipZero) continue;
    if (v !== v || v === Infinity || v === -Infinity) continue;

    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }

  if (lo === Infinity) return 0;
  if (lo === hi) return lo;

  // Compute histogram
  const bins = 1000;
  const scale = bins / (hi - lo);
  const hist = new Uint32Array(bins);

  let total = 0;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v === 0 && skipZero) continue;
    if (v !== v || v === Infinity || v === -Infinity) continue;

    let bin = (v - lo) * scale;
    bin = bin | 0;
    if (bin >= bins) bin = bins - 1;

    hist[bin]++;
    total++;
  }

  if (total === 0) return 0;

  // Find percentile value
  const target = (percentile / 100) * total;
  let cumulative = 0;
  for (let b = 0; b < bins; b++) {
    cumulative += hist[b];
    if (cumulative >= target) {
      return lo + b / scale;
    }
  }
  return hi;
}

function computeDbMagnitude(real: Int16Array, imag: Int16Array): Float32Array {
  const n = Math.min(real.length, imag.length);
  const db = new Float32Array(n);

  for (let i = 0; i < n; i++) {
    const re = real[i];
    const im = imag[i];
    const mag2 = re * re + im * im;
    db[i] = mag2 > 0 ? 10 * Math.log10(mag2) : -Infinity;
  }
  return db;
}

self.onmessage = async (event: MessageEvent<BandStretchRequest>) => {
  const {
    requestId,
    url,
    extent,
    sampleSize = 256,
    lowPercentile = 2,
    highPercentile = 98,
    isComplex = false,
  } = event.data;

  try {
    const tiff = await fromUrl(url, { allowFullFile: false });
    const image = await tiff.getImage();

    const imageWidth = image.getWidth();
    const imageHeight = image.getHeight();
    const rawSamples = image.getSamplesPerPixel();
    const singleBand = isComplex ? true : rawSamples === 1;

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
    const outWidth = Math.min(windowWidth, sampleSize);
    const outHeight = Math.min(windowHeight, sampleSize);

    const samplesToRead = isComplex
      ? [0, 1]
      : Array.from({ length: rawSamples }, (_, i) => i);

    const rasters = await image.readRasters({
      window,
      samples: samplesToRead,
      pool,
      width: outWidth,
      height: outHeight,
    });

    let bands: BandStretch[];

    if (isComplex) {
      const toInt16 = (r: unknown) =>
        r instanceof Int16Array
          ? r
          : new Int16Array((r as { buffer: ArrayBuffer }).buffer);

      const db = computeDbMagnitude(toInt16(rasters[0]), toInt16(rasters[1]));

      bands = [
        {
          min: computePercentile(db, lowPercentile),
          max: computePercentile(db, highPercentile),
          isLog: false,
        },
      ];
    } else {
      bands = (
        rasters as unknown as (Float32Array | Int16Array | Uint16Array)[]
      ).map((data) => ({
        min: computePercentile(data, lowPercentile),
        max: computePercentile(data, highPercentile),
        isLog: false,
      }));
    }

    const result: BandStretchResult = {
      type: "result",
      requestId,
      bands,
      singleBand,
      isComplex,
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
