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

interface ColorScheme {
  fill: (alpha?: number) => string;
  stroke: (alpha?: number) => string;
}

export const textColor = {
  fill: (alpha: number = 1.0) => `rgba(250,250,249,${alpha})`,
  stroke: (alpha: number = 1.0) => `rgba(28,25,23,${alpha})`,
};
export const equipmentColor = {
  fill: (alpha: number = 1.0) => `rgba(255,0,0,${alpha})`,
  stroke: (alpha: number = 1.0) => `rgba(255,255,255,${alpha})`,
};
export const activityColor = {
  fill: (alpha: number = 1.0) => `rgba(0,255,0,${alpha})`,
  stroke: (alpha: number = 1.0) => `rgba(255,255,255,${alpha})`,
};

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

export function styleAnnotationText(
  label: string,
  colorScheme: ColorScheme,
  alpha: number = 1.0,
  offsetY?: number | undefined,
) {
  return new Text({
    text: label,
    fill: new Fill({ color: colorScheme.fill(alpha) }),
    stroke: new Stroke({ color: colorScheme.stroke(alpha), width: 2 }),
    offsetY: offsetY,
  });
}

export function styleAnnotation(
  feature: FeatureLike,
  colorScheme: ColorScheme,
  alpha: number = 1.0,
  polygonAlpha: number | undefined = 0.0,
  strokeWidth: number = 1.0,
) {
  const geometry = feature.getGeometry();
  if (!(geometry instanceof Geometry)) return null;

  const label = feature.get("label");

  if (geometry instanceof Point) {
    return new Style({
      image: new Circle({
        radius: 5,
        fill: new Fill({ color: colorScheme.fill(alpha) }),
        stroke: new Stroke({
          color: equipmentColor.stroke(alpha),
          width: strokeWidth,
        }),
      }),
      text: label ? styleAnnotationText(label, textColor, 1.0, 25) : undefined,
    });
  }

  if (geometry instanceof Polygon || geometry instanceof MultiPolygon) {
    return new Style({
      stroke: new Stroke({
        color: colorScheme.fill(alpha),
        width: strokeWidth,
      }),
      fill:
        polygonAlpha === null
          ? undefined
          : new Fill({
              color: colorScheme.fill(polygonAlpha),
            }),
      text: label ? styleAnnotationText(label, textColor, 1.0, 10) : undefined,
    });
  }

  return null;
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

export const vertexStyle = new Style({
  image: new Circle({
    radius: 3,
    fill: new Fill({ color: "#fff" }),
    stroke: new Stroke({ color: "#000", width: 1 }),
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
