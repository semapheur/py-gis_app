import type { SourceSpecification, LayerSpecification } from "maplibre-gl";
import TileLayer from "ol/layer/Tile";
import XYZ from "ol/source/XYZ";
import TileWMS from "ol/source/TileWMS";
import WMTS, { optionsFromCapabilities } from "ol/source/WMTS";

export interface LayerInfo {
  id: string;
  label: string;
  visible: boolean;
}

export type XYZLayerConfig = {
  type: "xyz";
  id: string;
  label: string;
  url: string;
  tileSize?: number;
  maxzoom?: number;
  attribution?: string;
};

export type WMSLayerConfig = {
  type: "wms";
  id: string;
  label: string;
  url: string;
  layers: string;
  tileSize?: number;
  attribution?: string;
};

export type WMTSLayerConfig = {
  type: "wmts";
  id: string;
  label: string;
  url: string;
  tileSize?: number;
  attribution?: string;
};

export type MapLayerConfig = XYZLayerConfig | WMSLayerConfig | WMTSLayerConfig;

export type MapConfig = {
  layers: MapLayerConfig[];
};

function buildWMSTileUrl(url: string, layers: string): string {
  const params = new URLSearchParams({
    service: "WMS",
    version: "1.1.1",
    request: "GetMap",
    layers,
    bbox: "{bbox-epsg-3857}",
    width: "256",
    height: "256",
    srs: "EPSG:3857",
    format: "image/png",
    transparent: "true",
  });
  return `${url}?${params}`;
}

export function buildMapLibreStyle(layers: MapLayerConfig[]): {
  sources: Record<string, SourceSpecification>;
  layers: LayerSpecification[];
} {
  const sources: Record<string, SourceSpecification> = {};
  const mlLayers: LayerSpecification[] = [];

  for (const [index, layer] of layers.entries()) {
    switch (layer.type) {
      case "xyz":
        sources[layer.id] = {
          type: "raster",
          tiles: [layer.url],
          tileSize: layer.tileSize ?? 256,
          maxzoom: layer.maxzoom ?? 19,
          attribution: layer.attribution,
        };
        break;

      case "wms":
        sources[layer.id] = {
          type: "raster",
          tiles: [buildWMSTileUrl(layer.url, layer.layers)],
          tileSize: layer.tileSize ?? 256,
          attribution: layer.attribution,
        };
        break;

      case "wmts":
        sources[layer.id] = {
          type: "raster",
          tiles: [layer.url],
          tileSize: layer.tileSize ?? 256,
          attribution: layer.attribution,
        };
        break;
    }

    mlLayers.push({
      id: layer.id,
      type: "raster",
      source: layer.id,
      layout: {
        visibility: index === 0 ? "visible" : "none",
      },
    });
  }

  return { sources, layers: mlLayers };
}

export function buildOlLayers(layers: MapLayerConfig[]): TileLayer[] {
  return layers.map((layer, i) => {
    switch (layer.type) {
      case "xyz":
        return new TileLayer({
          visible: i === 0,
          source: new XYZ({
            url: layer.url,
            tileSize: layer.tileSize ?? 256,
            attributions: layer.attribution,
          }),
          properties: { id: layer.id, label: layer.label },
        });

      case "wms":
        return new TileLayer({
          visible: i === 0,
          source: new TileWMS({
            url: layer.url,
            params: {
              LAYERS: layer.layers,
              TILED: true,
            },
            attributions: layer.attribution,
          }),
          properties: { id: layer.id, label: layer.label },
        });

      case "wmts":
        return new TileLayer({
          visible: i === 0,
          source: new XYZ({
            url: layer.url,
            tileSize: layer.tileSize ?? 256,
            attributions: layer.attribution,
          }),
          properties: { id: layer.id, label: layer.label },
        });
    }
  });
}
