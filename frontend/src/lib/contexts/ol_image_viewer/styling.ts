import type { Coordinate } from "ol/coordinate";
import { type FeatureLike } from "ol/Feature";
import { Point, LineString, Polygon } from "ol/geom";
import { Projection, transform } from "ol/proj";
import { getArea, getLength } from "ol/sphere";
import { Circle, Fill, Stroke, Style, Text, RegularShape } from "ol/style";
import { vertexStyle } from "$lib/utils/ol_styles";

export interface Enhancement {
  brightness: number;
  contrast: number;
  exposure: number;
  saturation: number;
  gamma: number;
}

export const defaultEnhancement: Enhancement = {
  brightness: 0,
  contrast: 1,
  exposure: 0,
  saturation: 1,
  gamma: 1,
};

const rgbVariables = {
  rMin: 0,
  rMax: 255,
  gMin: 0,
  gMax: 255,
  bMin: 0,
  bMax: 255,
};

const stretchExpression = (bandR: number, bandG: number, bandB: number) => ({
  variables: { ...rgbVariables, ...defaultEnhancement },
  color: [
    "array",
    [
      "clamp",
      [
        "/",
        ["-", ["band", bandR], ["var", "rMin"]],
        ["-", ["var", "rMax"], ["var", "rMin"]],
      ],
      0,
      1,
    ],
    [
      "clamp",
      [
        "/",
        ["-", ["band", bandG], ["var", "gMin"]],
        ["-", ["var", "gMax"], ["var", "gMin"]],
      ],
      0,
      1,
    ],
    [
      "clamp",
      [
        "/",
        ["-", ["band", bandB], ["var", "bMin"]],
        ["-", ["var", "bMax"], ["var", "bMin"]],
      ],
      0,
      1,
    ],
    1,
  ],
  brightness: ["var", "brightness"],
  contrast: ["var", "contrast"],
  exposure: ["var", "exposure"],
  saturation: ["var", "saturation"],
  gamma: ["var", "gamma"],
});

export const multibandStyle = stretchExpression(1, 2, 3);
export const panchromaticStyle = stretchExpression(1, 1, 1);

const equipmentPointStyle = {
  base: {
    "circle-radius": 5,
    "circle-fill-color": "oklch(70.4% 0.191 22.216 / 0.5)",
    "circle-stroke-color": "rgba(255 255 255 / 0.5)",
    "circle-stroke-width": 1,
  },
  selected: {
    "circle-radius": 5,
    "circle-fill-color": "oklch(57.7% 0.245 27.325)",
    "circle-stroke-color": "rgba(255 255 255)",
    "circle-stroke-width": 2,
  },
};

const equipmentPolygonStyle = {
  base: {
    "stroke-color": "oklch(70.4% 0.191 22.216 / 0.5)",
    "stroke-width": 2,
    "fill-color": "rgba(0 0 0 / 0)",
  },
  selected: {
    "stroke-color": "oklch(70.4% 0.191 22.216)",
    "stroke-width": 1,
    "fill-color": "oklch(70.4% 0.191 22.216 / 0.1)",
  },
};

const selectFilter = [
  "any",
  ["==", ["var", "hoverId"], ["get", "id"]],
  ["==", ["get", "selected"], 1],
];

export const equipmentStyle = [
  {
    filter: ["all", ["==", ["geometry-type"], "Polygon"], selectFilter],
    style: equipmentPolygonStyle.selected,
  },
  {
    filter: ["all", ["==", ["geometry-type"], "Point"], selectFilter],
    style: equipmentPointStyle.selected,
  },
  {
    filter: ["==", ["geometry-type"], "Polygon"],
    style: equipmentPolygonStyle.base,
  },
  {
    filter: ["==", ["geometry-type"], "Point"],
    style: equipmentPointStyle.base,
  },
];

const ghostPointStyle = {
  base: {
    "circle-radius": 5,
    "circle-fill-color": "oklch(58.5% 0.233 277.117 / 0.5)",
    "circle-stroke-color": "rgba(0 0 0 / 0.5)",
    "circle-stroke-width": 1,
  },
  selected: {
    "circle-radius": 5,
    "circle-fill-color": "oklch(58.5% 0.233 277.117)",
    "circle-stroke-color": "rgba(0 0 0)",
    "circle-stroke-width": 2,
  },
};

const ghostPolygonStyle = {
  base: {
    "stroke-color": "oklch(58.5% 0.233 277.117 / 0.5)",
    "stroke-width": 2,
    "fill-color": "rgba(0 0 0 / 0)",
  },
  selected: {
    "stroke-color": "oklch(58.5% 0.233 277.117)",
    "stroke-width": 1,
    "fill-color": "oklch(58.5% 0.233 277.117 / 0.1)",
  },
};

export const ghostStyle = [
  {
    filter: ["all", ["==", ["geometry-type"], "Polygon"], selectFilter],
    style: ghostPolygonStyle.selected,
  },
  {
    filter: ["all", ["==", ["geometry-type"], "Point"], selectFilter],
    style: ghostPointStyle.selected,
  },
  {
    filter: ["==", ["geometry-type"], "Polygon"],
    style: ghostPolygonStyle.base,
  },
  {
    filter: ["==", ["geometry-type"], "Point"],
    style: ghostPointStyle.base,
  },
];

export function styleText(
  label: string,
  font: string,
  strokeWidth: number = 2,
  offsetY?: number | undefined,
) {
  return new Text({
    text: label,
    font,
    fill: new Fill({ color: "white" }),
    stroke: new Stroke({ color: "black", width: strokeWidth }),
    offsetY: offsetY,
  });
}

export function styleAnnotationLabel(
  feature: FeatureLike,
  select: boolean = false,
) {
  const geometry = feature.getGeometry()?.getType();
  if (!geometry) return null;

  const label = feature.get("label");
  if (!label) return null;

  const font = select ? "bold 10px sans-serif" : "10px sans-serif";
  const strokeWidth = select ? 3 : 2;
  const offsetY = geometry === "Point" ? 25 : 10;

  return new Style({
    text: styleText(label, font, strokeWidth, offsetY),
  });
}

const measurementStyle = new Style({
  fill: new Fill({
    color: "rgba(255 255 255 / 0)",
  }),
  stroke: new Stroke({
    color: "oklch(70.5% 0.213 47.604)",
    lineDash: [10, 10],
    width: 2,
  }),
  image: new Circle({
    radius: 5,
    stroke: new Stroke({
      color: "oklch(68.5% 0.169 237.323)",
    }),
    fill: new Fill({
      color: "rgba(255 255 255 / 0.2)",
    }),
  }),
});

const measurementActiveStyle = new Style({
  fill: new Fill({
    color: "rgba(255 255 255 / 0.1)",
  }),
  stroke: new Stroke({
    color: "oklch(70.5% 0.213 47.604)",
    width: 2,
  }),
  image: new Circle({
    radius: 5,
    stroke: new Stroke({
      color: "oklch(68.5% 0.169 237.323)",
    }),
    fill: new Fill({
      color: "rgba(255 255 255 / 0.2)",
    }),
  }),
});

const measurementLabelStyle = new Style({
  text: new Text({
    fill: new Fill({
      color: "rgba(255 255 255 / 1)",
    }),
    backgroundFill: new Fill({
      color: "rgba(0 0 0 / 0.7)",
    }),
    padding: [3, 3, 3, 3],
    textBaseline: "bottom",
    offsetY: -15,
  }),
  image: new RegularShape({
    radius: 8,
    points: 3,
    angle: Math.PI,
    displacement: [0, 10],
    fill: new Fill({
      color: "rgba(0 0 0 / 0.7)",
    }),
  }),
});

const measurementSegmentStyle = new Style({
  text: new Text({
    fill: new Fill({
      color: "rgba(255 255 255 / 1)",
    }),
    backgroundFill: new Fill({
      color: "rgba(0 0 0 / 0.4)",
    }),
    padding: [2, 2, 2, 2],
    textBaseline: "bottom",
    offsetY: -12,
  }),
  image: new RegularShape({
    radius: 6,
    points: 3,
    angle: Math.PI,
    displacement: [0, 8],
    fill: new Fill({
      color: "rgba(0 0 0 / 0.4)",
    }),
  }),
});

export function formatLength(line: LineString, projection: Projection): string {
  const length = getLength(line, { projection });

  const output =
    length > 1000
      ? `${(length / 1000).toFixed(2)} km`
      : `${length.toFixed(2)} m`;

  return output;
}

export function formatArea(polygon: Polygon, projection: Projection): string {
  const area = getArea(polygon, { projection });

  const output =
    area > 1_000_000
      ? `${(area / 1_000_000).toFixed(2)} km²`
      : `${area.toFixed(2)} m²`;

  return output;
}

function formatHeading(a: Coordinate, b: Coordinate, projection: Projection) {
  const [lon1, lat1] = transform(a, projection, "EPSG:4326");
  const [lon2, lat2] = transform(b, projection, "EPSG:4326");

  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const delta = ((lon2 - lon1) * Math.PI) / 180;

  const y = Math.sin(delta) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(delta);

  const theta = Math.atan2(y, x);
  const bearing = ((theta * 180) / Math.PI + 360) % 360;

  return `${bearing.toFixed(1)}°`;
}

export function styleMeasurement(
  projection: Projection,
  feature: FeatureLike,
  segments: boolean,
  active: boolean = false,
  selected: boolean = false,
) {
  const styles = [active ? measurementActiveStyle : measurementStyle];

  if (selected) {
    styles.push(vertexStyle);
  }

  const geometry = feature.getGeometry();
  if (!geometry) return styles;

  const type = geometry.getType();

  let point: Point | undefined;
  let label: string | undefined;
  let line: LineString | undefined;

  if (type === "Polygon") {
    const polygon = geometry as Polygon;
    point = polygon.getInteriorPoint();
    label = formatArea(polygon, projection);
    line = new LineString(polygon.getCoordinates()[0]);
  } else if (type === "LineString") {
    const lineString = geometry as LineString;
    point = new Point(lineString.getLastCoordinate());
    label = formatLength(lineString, projection);
    line = lineString;
  }

  if (segments && line) {
    line.forEachSegment((a, b) => {
      const segment = new LineString([a, b]);
      const segmentLength = formatLength(segment, projection);
      const segmentHeading = formatHeading(a, b, projection);
      const segmentLabel = `${segmentLength}\n${segmentHeading}`;
      const segmentPoint = new Point(segment.getCoordinateAt(0.5));

      const segmentStyle = measurementSegmentStyle.clone();
      segmentStyle.setGeometry(segmentPoint);
      segmentStyle.getText()?.setText(segmentLabel);
      styles.push(segmentStyle);
    });
  }

  if (label && point) {
    const labelStyle = measurementLabelStyle.clone();
    labelStyle.setGeometry(point);
    labelStyle.getText()?.setText(label);
    styles.push(labelStyle);
  }

  return styles;
}

export function styleSearchMarker(feature: FeatureLike) {
  const label = feature.get("label") ?? "";
  return new Style({
    image: new Circle({
      radius: 5,
      fill: new Fill({ color: "rgb(255 240 40)" }),
      stroke: new Stroke({ color: "rgb(0 0 0)", width: 1 }),
    }),
    text: new Text({
      text: label,
      offsetY: -12,
      font: "11px sans-serif",
      fill: new Fill({ color: "rgb(255 255 255)" }),
      stroke: new Stroke({ color: "rgb(0 0 0)", width: 1 }),
    }),
  });
}
