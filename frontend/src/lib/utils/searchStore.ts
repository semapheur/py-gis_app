const store = new Map<string, GeoJSON.Polygon>();

export function savePolygon(polygon: GeoJSON.Polygon) {
  const id = crypto.randomUUID();
  store.set(id, polygon);
  return id;
}

export function getPolygon(id: string): GeoJSON.Polygon | null {
  return store.get(id) ?? null;
}
