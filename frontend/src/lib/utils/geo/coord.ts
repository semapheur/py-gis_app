import { Parser } from "@openaip/coordinate-parser";
import { UTM } from "$lib/utils/geo/utm";
import { MGRS } from "$lib/utils/geo/mgrs";
import { LatLon } from "$lib/utils/geo/latlon";

export type Coordinate = LatLon | UTM | MGRS;

function parseLatLon(latlonText: string): LatLon {
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

  return new LatLon(latlon.longitude, latlon.latitude);
}

export function parseUtm(utmText: string) {
  return UTM.parse(utmText);
}

export function parseMgrs(mgrsText: string) {
  return MGRS.parse(mgrsText);
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
  return tryParsers<Coordinate>(coordinateText, [
    parseLatLon,
    parseUtm,
    parseMgrs,
  ]);
}
