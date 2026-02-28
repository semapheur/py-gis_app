import { type FeatureLike } from "ol/Feature";
import {
  Geometry,
  Point,
  LineString,
  Polygon,
  MultiPoint,
  MultiPolygon,
} from "ol/geom";
import { Projection } from "ol/proj";
import { getArea, getLength } from "ol/sphere";
import { Circle, Fill, Stroke, Style, Text, RegularShape } from "ol/style";

const equipmentPointStyle = {
  base: {
    "circle-radius": 5,
    "circle-fill-color": "oklch(57.7% 0.245 27.325 / 0.5)",
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
    "stroke-color": "oklch(57.7% 0.245 27.325 / 0.5)",
    "stroke-Width": 2,
  },
  selected: {
    "stroke-color": "oklch(57.7% 0.245 27.325)",
    "stroke-width": 3,
    "fill-color": "oklch(57.7% 0.245 27.325 / 0.1)",
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

export const vertexStyle = new Style({
  image: new Circle({
    radius: 3,
    fill: new Fill({ color: "white" }),
    stroke: new Stroke({ color: "black", width: 1 }),
  }),
  geometry: (feature: FeatureLike) => {
    const geometry = feature.getGeometry();

    if (geometry instanceof Polygon) {
      return new MultiPoint(geometry.getCoordinates()[0]);
    }

    if (geometry instanceof MultiPolygon) {
      return new MultiPoint(geometry.getCoordinates().flatMap((p) => p[0]));
    }
  },
});

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
    color: "rgba(255, 255, 255, 0.2)",
  }),
  stroke: new Stroke({
    color: "rgba(0, 0, 0, 0.5)",
    lineDash: [10, 10],
    width: 2,
  }),
  image: new Circle({
    radius: 5,
    stroke: new Stroke({
      color: "rgba(0, 0, 0, 0.7)",
    }),
    fill: new Fill({
      color: "rgba(255, 255, 255, 0.2)",
    }),
  }),
});

const measurementLabelStyle = new Style({
  text: new Text({
    fill: new Fill({
      color: "rgba(255, 255, 255, 1)",
    }),
    backgroundFill: new Fill({
      color: "rgba(0, 0, 0, 0.7)",
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
      color: "rgba(0, 0, 0, 0.7)",
    }),
  }),
});

const measurementSegmentStyle = new Style({
  text: new Text({
    fill: new Fill({
      color: "rgba(255, 255, 255, 1)",
    }),
    backgroundFill: new Fill({
      color: "rgba(0, 0, 0, 0.4)",
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
      color: "rgba(0, 0, 0, 0.4)",
    }),
  }),
});

function formatLength(line: LineString, projection: Projection): string {
  const length = getLength(line, { projection });

  const output =
    length > 1000
      ? `${(length / 1000).toFixed(2)} km`
      : `${length.toFixed(2)} m`;

  return output;
}

function formatArea(polygon: Polygon, projection: Projection): string {
  const area = getArea(polygon, { projection });

  const output =
    area > 10000
      ? `${(area / 1000000).toFixed(2)} km²`
      : `${area.toFixed(2)} m²`;

  return output;
}

export function styleMeasurement(
  projection: Projection,
  feature: FeatureLike,
  segments: boolean,
) {
  const styles = [measurementStyle];
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
      const segmentLabel = formatLength(segment, projection);
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
    labelStyle.getText().setText(label);
    styles.push(labelStyle);
  }

  return styles;
}
