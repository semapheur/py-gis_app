import { type FeatureLike } from "ol/Feature";
import { MultiPoint, LineString, Polygon, MultiPolygon } from "ol/geom";
import { Circle, Fill, Stroke, Style } from "ol/style";

const vertexCircle = new Circle({
  radius: 3,
  fill: new Fill({ color: "white" }),
  stroke: new Stroke({ color: "black", width: 1 }),
});

export const vertexStyle = new Style({
  image: vertexCircle,
  geometry: (feature: FeatureLike) => {
    const geometry = feature.getGeometry();

    if (geometry instanceof LineString) {
      return new MultiPoint(geometry.getCoordinates());
    }

    if (geometry instanceof Polygon) {
      return new MultiPoint(geometry.getCoordinates()[0]);
    }

    if (geometry instanceof MultiPolygon) {
      return new MultiPoint(geometry.getCoordinates().flatMap((p) => p[0]));
    }
  },
});
