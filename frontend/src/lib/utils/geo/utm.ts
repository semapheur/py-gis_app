import proj4 from "proj4";
import { LatLon } from "$lib/utils/geo/latlon";

const hemisphereCodes = {
  N: "north",
  S: "south",
} as const;

type Hemisphere = (typeof hemisphereCodes)[keyof typeof hemisphereCodes];

export class UTM {
  readonly #zone: number;
  readonly #hemisphere: Hemisphere;
  readonly #easting: number;
  readonly #northing: number;

  static readonly #utmPattern =
    /^(?<zone>\d{1,2})\s*(?:(?<hemisphere>[NS])|(?<band>[C-HJ-NP-X]))\s*(?<easting>\d+(?:\.\d+)?)m?\s*E?\s*(?<northing>\d+(?:\.\d+)?)m?\s*N?$/i;

  constructor(
    zone: number,
    hemisphere: Hemisphere,
    easting: number,
    northing: number,
  ) {
    this.#zone = zone;
    UTM.validateZone(zone);
    this.#hemisphere = hemisphere;
    this.#easting = easting;
    this.#northing = northing;
  }

  get northing() {
    return this.#northing;
  }

  public static parse(utm: string): UTM {
    const matches = utm.trim().match(UTM.#utmPattern);
    if (!matches?.groups) {
      throw new Error(`Invalid UTM: ${utm}`);
    }

    const zone = parseInt(matches.groups.zone);

    const hemi = matches.groups.hemisphere;
    const band = matches.groups.band;

    const hemisphere: Hemisphere = hemi
      ? hemisphereCodes[hemi as "N" | "S"]
      : UTM.getHemisphere(band);

    const easting = parseFloat(matches.groups.easting);
    const northing = parseFloat(matches.groups.northing);

    return new UTM(zone, hemisphere, easting, northing);
  }

  public toLatLon(): LatLon {
    const utmProjection = `+proj=utm +zone=${this.#zone} +${this.#hemisphere} +datum=WGS84 +units=m +no_defs`;
    const wgs84Projection = proj4("WGS84");

    const [lon, lat] = proj4(utmProjection, wgs84Projection, [
      this.#easting,
      this.#northing,
    ]);

    return new LatLon(lon, lat);
  }

  public static getHemisphere(band: string) {
    return band.charCodeAt(0) < "N".charCodeAt(0)
      ? hemisphereCodes.N
      : hemisphereCodes.S;
  }

  public static fromGeographic(lon: number, lat: number) {
    const zone = Math.floor((lon + 180) / 6) + 1;
    const hemisphere = lat >= 0 ? "north" : "south";

    const utmProjection = `+proj=utm +zone=${zone} +${hemisphere} +datum=WGS84 +units=m +no_defs`;
    const wgs84Projection = proj4("WGS84");

    const [easting, northing] = proj4(wgs84Projection, utmProjection, [
      lon,
      lat,
    ]);

    return new UTM(zone, hemisphere, easting, northing);
  }

  public static validateZone(zone: number) {
    if (zone < 1 || zone > 60) {
      throw new Error(`Invalid MGRS zone (1-60): ${zone}`);
    }
  }
}
