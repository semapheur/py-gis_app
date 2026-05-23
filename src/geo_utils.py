def utm_from_gcps(gcp_list: list[dict]) -> str:
  lons = [gcp["x"] for gcp in gcp_list]
  lats = [gcp["y"] for gcp in gcp_list]

  lon_centre = sum(lons) / len(lons)
  lat_centre = sum(lats) / len(lats)

  zone = int((lon_centre + 180) / 6) + 1
  epsg = 32600 + zone if lat_centre >= 0 else 32700 + zone
  return f"EPSG:{epsg}"
