def utm_from_gcps(gcp_list: list[dict]) -> str:
  lons = [gcp["x"] for gcp in gcp_list]
  lats = [gcp["y"] for gcp in gcp_list]

  lon_centre = sum(lons) / len(lons)
  lat_centre = sum(lats) / len(lats)

  zone = int((lon_centre + 180) / 6) + 1
  epsg = 32600 + zone if lat_centre >= 0 else 32700 + zone
  return f"EPSG:{epsg}"


def rpc_polynomial(coefficients: list[float], L: float, P: float, H: float) -> float:
  return (
    coefficients[0]
    + coefficients[1] * L
    + coefficients[2] * P
    + coefficients[3] * H
    + coefficients[4] * L * P
    + coefficients[5] * L * H
    + coefficients[6] * P * H
    + coefficients[7] * L * L
    + coefficients[8] * P * P
    + coefficients[9] * H * H
    + coefficients[10] * P * L * H
    + coefficients[11] * L**3
    + coefficients[12] * L * P * P
    + coefficients[13] * L * H * H
    + coefficients[14] * L * L * P
    + coefficients[15] * P**3
    + coefficients[16] * P * H * H
    + coefficients[17] * L * L * H
    + coefficients[18] * P * P * H
    + coefficients[19] * H**3
  )
