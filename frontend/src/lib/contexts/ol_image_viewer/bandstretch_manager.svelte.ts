import type { Map } from "ol";
import type WebGLTileLayer from "ol/layer/WebGLTile";
import type {
  BandStretchRequest,
  BandStretchResult,
  BandStretchError,
  Extent,
} from "$lib/workers/bandstretch.worker";
import type { BandStatistics } from "$lib/utils/types";

function isComplexBand(band: BandStatistics): boolean {
  return band.data_type.toLowerCase().startsWith("c");
}

function stretchRange(band: BandStatistics) {
  if (isComplexBand(band)) {
    const amplitudeScale = band.stddev * Math.SQRT2;
    return { min: 0, max: amplitudeScale * 4 };
  }

  return { min: band.min, max: band.max };
}

export function buildStyleExpression(
  bands: BandStatistics[],
): Record<string, unknown> {
  const stretch = (bandIndex: number) => {
    const { min, max } = stretchRange(bands[bandIndex - 1]);
    const range = max - min || 1;
    return ["clamp", ["/", ["-", ["band", bandIndex], min], range], 0, 1];
  };

  const singleBand = bands.length === 1;
  const raw = singleBand
    ? { r: stretch(1), g: stretch(1), b: stretch(1) }
    : { r: stretch(1), g: stretch(2), b: stretch(3) };

  const gamma = (channel: unknown) => [
    "^",
    ["clamp", ["*", channel, ["^", 2, ["var", "exposure"]]], 0, 1],
    ["/", 1, ["var", "gamma"]],
  ];

  const gammaExposed = {
    r: gamma(raw.r),
    g: gamma(raw.g),
    b: gamma(raw.b),
  };

  const saturated = singleBand
    ? gammaExposed
    : (() => {
        const luma = [
          "+",
          ["*", 0.2126, gammaExposed.r],
          ["*", 0.7152, gammaExposed.g],
          ["*", 0.0722, gammaExposed.b],
        ];

        const saturation = (channel: unknown) => [
          "clamp",
          ["+", luma, ["*", ["var", "saturation"], ["-", channel, luma]]],
          0,
          1,
        ];

        return {
          r: saturation(gammaExposed.r),
          g: saturation(gammaExposed.g),
          b: saturation(gammaExposed.b),
        };
      })();

  const enhance = (channel: unknown) => [
    "clamp",
    [
      "+",
      ["var", "brightness"],
      ["*", ["var", "contrast"], ["-", channel, 0.5]],
      0.5,
    ],
    0,
    1,
  ];

  return {
    color: [
      "array",
      enhance(saturated.r),
      enhance(saturated.g),
      enhance(saturated.b),
      1,
    ],
  };
}

function _buildStyleExpression(
  result: BandStretchResult,
): Record<string, unknown> {
  const { bands, singleBand, isComplex } = result;

  const linearStretch = (bandIndex: number) => {
    const { min, max } = bands[bandIndex - 1] ?? { min: 0, max: 0 };
    const range = max - min || 1;
    return ["clamp", ["/", ["-", ["band", bandIndex], min], range], 0, 1];
  };

  const logStretch = () => {
    const { min: minDb, maxDb } = bands[0] ?? { min: -30, max: 0 };
    const rangeDb = maxDb - minDb || 1;

    const re: unknown[] = ["band", 1];
    const im: unknown[] = ["band", 2];

    const mag2: unknown[] = ["+", ["*", re, re], ["*", im, im]];

    const powerDb: unknown[] = [
      "*",
      10,
      ["log", ["/", ["max", mag2, 1e-10], Math.LN10]],
    ];
    const log10Expr: unknown[] = [
      "/",
      ["log", ["max", mag2, 1e-10], Math.LN10],
    ];
    const powerDb10: unknown[] = ["*", 10, log10Expr];
    const stretched: unknown[] = [
      "clamp",
      ["/", ["-", powerDb10, minDb], rangeDb],
      0,
      1,
    ];
    return stretched;
  };

  if (isComplex) {
    const s = logStretch();
    return { color: ["array", s, s, s, 1] };
  }

  return {
    color: ["array", linearStretch(1), linearStretch(2), linearStretch(3), 1],
  };
}

export class BandStretchManager {
  isComputing = $state(false);
  lastStretch = $state<BandStretchResult | null>(null);
  error = $state<string | null>(null);

  readonly #layer: WebGLTileLayer;
  readonly #map: Map;
  readonly #url: string;

  #worker: Worker | null = null;
  #pendingRequestId: string | null = null;
  #debounceTimer: ReturnType<typeof setTimeout> | null = null;
  #moveendKey: import("ol/events").EventsKey | null = null;

  #debounceMs: number;

  #lowPercentile: number;
  #highPercentile: number;

  #sampleSize: number;

  constructor(
    layer: WebGLTileLayer,
    map: Map,
    url: string,
    options: {
      debounceMs?: number;
      lowPercentile?: number;
      highPercentile?: number;
      sampleSize?: number;
    } = {},
  ) {
    this.#layer = layer;
    this.#map = map;
    this.#url = url;
    this.#debounceMs = options.debounceMs ?? 400;
    this.#lowPercentile = options.lowPercentile ?? 2;
    this.#highPercentile = options.highPercentile ?? 98;
    this.#sampleSize = options.sampleSize ?? 256;
  }

  start() {
    if (this.#worker) return;

    this.#worker = new Worker(
      new URL("$lib/workers/bandstretch.worker.ts", import.meta.url),
      { type: "module" },
    );

    this.#worker.onmessage = this.#handleMessage.bind(this);
    this.#worker.onerror = (e) => {
      this.error = e.message;
      this.isComputing = false;
    };

    this.#moveendKey = this.#map.on("moveend", () => this.#scheduleRecompute());

    const source = (this.#layer as any).getSource?.();
    if (!source || source.getState() === "ready") {
      this.#scheduleRecompute(0);
    } else {
      const onSourceChange = () => {
        if (source.getState() === "ready") {
          source.un("change", onSourceChange);
          this.#scheduleRecompute();
        }
      };
      source.on("change", onSourceChange);
    }

    this.#scheduleRecompute(0);
  }

  stop() {
    if (this.#debounceTimer) clearTimeout(this.#debounceTimer);

    if (this.#moveendKey) {
      import("ol/events").then(({ unlistenByKey }) =>
        unlistenByKey(this.#moveendKey!),
      );
      this.#moveendKey = null;
    }

    this.#worker?.terminate();
    this.#worker = null;
    this.isComputing = false;
  }

  recompute() {
    this.#scheduleRecompute(0);
  }

  #scheduleRecompute(delay = this.#debounceMs) {
    if (this.#debounceTimer) clearTimeout(this.#debounceTimer);
    this.#debounceTimer = setTimeout(() => this.#dispatch(), delay);
  }

  #dispatch() {
    if (!this.#worker) return;

    const view = this.#map.getView();

    if (!view.getCenter()) return;

    const extent = view.calculateExtent(
      this.#map.getSize() ?? [0, 0],
    ) as Extent;

    const requestId = crypto.randomUUID();
    this.#pendingRequestId = requestId;
    this.isComputing = true;
    this.error = null;

    const request: BandStretchRequest = {
      requestId,
      url: this.#url,
      extent,
      sampleSize: this.#sampleSize,
      lowPercentile: this.#lowPercentile,
      highPercentile: this.#highPercentile,
    };

    this.#worker.postMessage(request);
  }

  #handleMessage(event: MessageEvent<BandStretchResult | BandStretchError>) {
    const msg = event.data;

    if (msg.requestId != this.#pendingRequestId) return;

    this.isComputing = false;

    if (msg.type === "error") {
      this.error = msg.message;
      return;
    }

    this.lastStretch = msg;
    console.log(msg);
    this.#applyStretch(msg);
  }

  #applyStretch(result: BandStretchResult) {
    const style = _buildStyleExpression(result);
    (this.#layer as any).setStyle(style);
  }
}
