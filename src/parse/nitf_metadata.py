def get_nitf_info(nitf_data: dict):

  classification = nitf_data.get("FSCLAS")
  releasability = nitf_data.get("FSREL")
  codewords = nitf_data.get("FSCODE")

  return {
    "classification": classification,
    "releasability": releasability,
    # "datetime_collected": datetime_collected,
    # "sensor_name": iceye_data["satellite_name"],
    # "footprint": footprint,
    # "look_angle": iceye_data["satellite_look_angle"],
    # "azimuth_angle": azimuth_angle,
    # "ground_sample_distance_row": iceye_data["azimuth_spacing"],
    # "ground_sample_distance_col": iceye_data["range_spacing"],
    # "interpretation_rating": None,
  }
