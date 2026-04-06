export type BBox = [west: number, south: number, east: number, north: number];

export function parseBbox(raw: string): BBox | null {
  const parts = raw.split(",").map(Number);
  if (parts.length !== 4 || parts.some(isNaN)) return null;

  return parts as BBox;
}

export function bboxToWkt(bbox: BBox, decimals: number = 6): string {
  const f = 10 ** decimals;

  const [west, south, east, north] = bbox;

  const x1 = Math.round(west * f) / f;
  const y1 = Math.round(south * f) / f;
  const x2 = Math.round(east * f) / f;
  const y2 = Math.round(north * f) / f;

  return `POLYGON((${[
    `${x1} ${y1}`,
    `${x2} ${y1}`,
    `${x2} ${y2}`,
    `${x1} ${y2}`,
    `${x1} ${y1}`,
  ].join(", ")}))`;
}

export function wktToBbox(wkt: string): BBox {
  const match = wkt.trim().match(/^POLYGON\s*\(\(s*(.+?)\s*\)\)$/i);

  if (!match) {
    throw new Error(`Invalid WKT POLYGON: ${wkt}`);
  }

  const coordText = match[1];

  const coords = coordText
    .split(",")
    .map((pair) => pair.trim().split(/\s+/).map(Number));

  if (coords.length < 4) {
    throw new Error(
      `WKT polygon must have at least 4 coordinate pairs. Provided WKT has ${coords.length}: ${wkt}`,
    );
  }

  const lons = coords.map(([lon]) => lon);
  const lats = coords.map(([, lat]) => lat);

  const west = Math.min(...lons);
  const east = Math.max(...lons);
  const south = Math.min(...lats);
  const north = Math.max(...lats);

  return [west, south, east, north];
}
