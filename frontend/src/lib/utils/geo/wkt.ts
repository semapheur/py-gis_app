type Coordinate = number[];
type Ring = Coordinate[];
type Polygon = {
  type: "Polygon";
  coordinates: Ring[];
};

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

export class WktParser {
  #input: string;
  #position: number = 0;

  constructor(input: string) {
    this.#input = input;
  }

  private match(pattern: RegExp): string | null {
    const flags = pattern.flags.includes("y")
      ? pattern.flags
      : pattern.flags + "y";
    const regex = new RegExp(pattern.source, flags);
    regex.lastIndex = this.#position;

    const match = regex.exec(this.#input);
    if (!match) return null;

    this.#position = regex.lastIndex;
    return match[0];
  }

  private skipWhitespace(): void {
    this.match(/\s*/y);
  }

  private parseMultiCoords(): Ring[] | null {
    this.skipWhitespace();
    if (!this.match(/\(/y)) return null;

    const rings: Ring[] = [];

    while (true) {
      this.skipWhitespace();

      if (this.match(/\(/y)) {
        const ring: Ring = [];
        while (true) {
          this.skipWhitespace();
          // Match Lng Lat pair
          const pointMatch = this.match(
            /-?\d*\.?\d+(?:[eE][-+]?\d+)?\s+-?\d*\.?\d+(?:[eE][-+]?\d+)?/y,
          );
          if (!pointMatch) break;

          const coords = pointMatch.trim().split(/\s+/).map(Number);
          ring.push([coords[0], coords[1]]);

          this.skipWhitespace();
          if (!this.match(/,/y)) break;
        }

        if (!this.match(/\)/y)) return null; // Error: Missing closing ring paren
        rings.push(ring);
      }

      this.skipWhitespace();
      if (this.match(/,/y)) continue;
      if (this.match(/\)/y)) break;
      return null; // Error: Unexpected character
    }
    return rings;
  }

  public parsePolygon(): { type: "Polygon"; coordinates: number[][][] } | null {
    if (!this.match(/polygon(\s[zm])?/iy)) return null;
    this.skipWhitespace();

    if (this.match(/empty/iy)) {
      return {
        type: "Polygon",
        coordinates: [],
      };
    }

    const coordinates = this.parseMultiCoords();
    if (!coordinates) return null;

    return {
      type: "Polygon",
      coordinates,
    };
  }
}
