import { splitFloat } from "$lib/utils/math";

type LatLonFormat = "dms" | "ddm" | "dd";

function formatFloat(float: number, decimals: number | null) {
  return decimals === null ? float.toString() : float.toFixed(decimals);
}

export class LatLon {
  readonly #longitude: number;
  readonly #latitude: number;

  constructor(longitude: number, latitude: number) {
    const { normalizedLatitude, flipLongitude } =
      LatLon.normalizeLatitude(latitude);

    let normalizedLongitude = LatLon.normalizeLongitude(longitude);
    if (flipLongitude) {
      normalizedLongitude *= -1;
    }

    this.#longitude = normalizedLongitude;
    this.#latitude = normalizedLatitude;
  }

  get latitude() {
    return this.#latitude;
  }

  get longitude() {
    return this.#longitude;
  }

  public print(
    format: LatLonFormat,
    decimals: number | null = null,
    separator: string = " ",
  ) {
    const latHem = Math.sign(this.#latitude) >= 0 ? "N" : "S";
    const lonHem = Math.sign(this.#longitude) >= 0 ? "E" : "W";

    if (format === "dd") {
      const lat = Math.abs(this.#latitude);
      const lon = Math.abs(this.#longitude);

      return `${formatFloat(lat, decimals)}°${latHem}${separator}${formatFloat(lon, decimals)}°${lonHem}`;
    }

    if (format === "ddm") {
      const lat = LatLon.toDDM(this.#latitude);
      const lon = LatLon.toDDM(this.#longitude);

      const latText = `${lat.d}°${formatFloat(lat.m, decimals)}'${latHem}`;
      const lonText = `${lon.d}°${formatFloat(lon.m, decimals)}'${lonHem}`;
      return `${latText}${separator}${lonText}`;
    }

    if (format === "dms") {
      const lat = LatLon.toDMS(this.#latitude);
      const lon = LatLon.toDMS(this.#longitude);

      const latText = `${lat.d}°${lat.m}'${formatFloat(lat.s, decimals)}''${latHem}`;
      const lonText = `${lon.d}°${lon.m}'${formatFloat(lon.s, decimals)}''${lonHem}`;
      return `${latText}${separator}${lonText}`;
    }
  }

  public toWkt(decimals: number | null = null) {
    return `POINT(${formatFloat(this.#longitude, decimals)},${formatFloat(this.#latitude, decimals)})`;
  }

  private static normalizeLongitude(lon: number): number {
    // Wrap into (-180, 180]
    const wrapped = ((((lon + 180) % 360) + 360) % 360) - 180;

    // Special case: map -180 to +180 to satisfy the interval (-180, 180]
    return wrapped === -180 ? 180 : wrapped;
  }

  private static normalizeLatitude(lat: number) {
    // Wrap into (-180, 180]
    const wrapped = ((((lat + 180) % 360) + 360) % 360) - 180;

    if (wrapped > 90) {
      return { normalizedLatitude: 180 - wrapped, flipLongitude: true };
    }
    if (wrapped < -90) {
      return { normalizedLatitude: -180 - wrapped, flipLongitude: true };
    }

    return { normalizedLatitude: wrapped, flipLongitude: false };
  }

  private static toDDM(value: number) {
    const abs = Math.abs(value);
    const d = Math.floor(abs);
    const m = (abs - d) * 60;

    return { d, m };
  }

  private static toDMS(value: number) {
    const { d, m: minFloat } = LatLon.toDDM(value);

    const m = Math.floor(minFloat);
    const s = (minFloat - m) * 60;

    return { d, m, s };
  }
}
