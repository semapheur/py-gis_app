import proj4 from "proj4";
import { Parser } from "@openaip/coordinate-parser";

export type BBox = [
  minLng: number,
  minLat: number,
  maxLng: number,
  maxLat: number,
];

export function bboxToWkt(bbox: BBox, decimals: number = 6): string {
  const f = 10 ** decimals;

  const [minLng, minLat, maxLng, maxLat] = bbox;

  const x1 = Math.round(minLng * f) / f;
  const y1 = Math.round(minLat * f) / f;
  const x2 = Math.round(maxLng * f) / f;
  const y2 = Math.round(maxLat * f) / f;

  return `POLYGON((${[
    `${x1} ${y1}`,
    `${x2} ${y1}`,
    `${x2} ${y2}`,
    `${x1} ${y2}`,
    `${x1} ${y1}`,
  ].join(", ")}))`;
}

export function polygonToWkt(
  polygon: GeoJSON.Polygon,
  decimals: number = 6,
): string {
  const f = 10 ** decimals;

  const ring = polygon.coordinates[0];

  const coords = ring
    .map(([lng, lat]) => {
      const x = Math.round(lng * f) / f;
      const y = Math.round(lat * f) / f;
      return `${x} ${y}`;
    })
    .join(", ");
  return `POLYGON((${coords}))`;
}

function wktToGeoJSONPolygon(wkt: string): GeoJSON.Polygon {
  const trimmed = wkt.trim();

  if (!trimmed.startsWith("POLYGON")) {
    throw new Error("Only POLYGON WKT is supported");
  }

  const match = trimmed.match(/^POLYGON\s*\(\(\s*(.+?)\s*\)\)$/i);
  if (!match) {
    throw new Error("Invalid POLYGON WKT");
  }

  const coordsText = match[1];

  const coordinates: GeoJSON.Position[] = coordsText.split(",").map((pair) => {
    const [lng, lat] = pair.trim().split(/\s+/).map(Number);
    if (Number.isNaN(lng) || Number.isNaN(lat)) {
      throw new Error(`Invalid coordinate pair: ${pair}`);
    }
    return [lng, lat];
  });

  return {
    type: "Polygon",
    coordinates: [coordinates],
  };
}

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

export function parseLatLon(latlonText: string) {
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

export function parseCoordinates(coordinateText: string) {
  return parseLatLon(coordinateText) || utmToLatLon(coordinateText);
}
