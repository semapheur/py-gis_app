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
