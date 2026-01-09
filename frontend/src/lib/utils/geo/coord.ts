import { Parser } from "@openaip/coordinate-parser";
import { UTM } from "$lib/utils/geo/utm";
import { MGRS } from "$lib/utils/geo/mgrs";

function parseLatLon(latlonText: string) {
  const m = latlonText
    .trim()
    .match(
      /\d{1,2} \d{1,2} \d{1,2}(\.\d+)?[NSEW][ ,]\d{1,3} \d{1,2} \d{1,2}(\.\d+)?[NSEW]/,
    );

  if (m) {
    latlonText = latlonText.replaceAll(/(?<=\d) (?=\d)/g, ":");
    console.log(latlonText);
  }

  const parser = new Parser();
  const latlon = parser.parse(latlonText.trim());

  return [latlon.longitude, latlon.latitude];
}

export function parseUtm(utmText: string) {
  const utm = UTM.parse(utmText);
  console.log(utm.toPoint());
}

function tryParsers<T>(value: string, parsers: Array<(v: string) => T>): T {
  for (const parse of parsers) {
    try {
      return parse(value);
    } catch {}
  }
  throw new Error(`No parser could handle: ${value}`);
}

export function parseCoordinates(coordinateText: string) {
  return tryParsers(coordinateText, [parseLatLon, utmToLatLon]);
}

/* Convert UTM to lat/lon with proj4
import proj4 from "proj4";

interface UTM {
  zone: number;
  band: string;
  easting: number;
  northing: number;
}

function utmBandToHemisphere(band: string): "north" | "south" {
  if (!band || band.length !== 1) {
    throw new Error("Latitude band must be a single letter");
  }

  const letter = band.toUpperCase();

  if (letter < "C" || letter > "X" || letter === "I" || letter === "O") {
    throw new Error(`Ìnvalid UTM latitude band: ${band}`);
  }

  return letter >= "N" ? "north" : "south";
}

function parseUtm(utmText: string) {
  const match = utmText
    .trim()
    .match(/^(\d{1,2})([C-HJ-NP-X])\s+(\d+)\s+(\d+)$/);

  if (!match) return null;

  const [, zone, band, easting, northing] = match;

  return {
    zone: parseInt(zone),
    band,
    easting: parseInt(easting),
    northing: parseInt(northing),
  };
}

export function utmToLatLon(utmText: string): [number, number] {
  const utm = parseUtm(utmText);

  if (!utm) {
    throw new Error(`Invalid UTM coordinate: ${text}`);
  }

  const hemisphere = utmBandToHemisphere(utm.band);

  const utmProjection = `+proj=utm +zone=${utm.zone} +${hemisphere} +datum=WGS84 +units=m +no_defs`;
  const wgs84Projection = proj4("WGS84");

  return proj4(utmProjection, wgs84Projection, [utm.easting, utm.northing]);
}
*/
