import type { Map } from "ol";
import type WebGLTileLayer from "ol/layer/WebGLTile";
import type {
  BandStretchRequest,
  BandStretchResult,
  BandStretchError,
  Extent,
} from "$lib/workers/bandstretch.worker";

function buildStyleExpression(
  result: BandStretchResult,
): Record<string, unknown> {
  const { bands, singleBand } = result;

  const stretch = (bandIndex: number) => {
    const { min, max } = bands[bandIndex - 1] ?? { min: 0, max: 1 };
    const range = max - min || 1;
    return ["clamp", ["/", ["-", ["band", bandIndex], min], range], 0, 1];
  };

  if (singleBand) {
    const s = stretch(1);
    return { color: ["array", s, s, s, 1] };
  }

  return {
    color: ["array", stretch(1), stretch(2), stretch(3), 1],
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
    const style = buildStyleExpression(result);
    (this.#layer as any).setStyle(style);
  }
}
