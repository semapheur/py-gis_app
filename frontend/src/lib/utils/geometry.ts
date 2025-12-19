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
