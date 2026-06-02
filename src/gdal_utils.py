import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Optional, TypedDict, Union, cast

ResampleAlgorithms = Literal[
  "nearest",
  "bilinear",
  "cubic",
  "cubicspline",
  "lanczos",
  "average",
  "rms",
  "mode",
  "max",
  "min",
  "med",
  "q1",
  "q3",
  "sum",
]

ColorInterp = Literal[
  "red",
  "green",
  "blue",
  "alpha",
  "gray",
  "undefined",
  "pan",
  "coastal",
  "rededge",
  "nir",
  "swir",
  "mwir",
  "lwir",
]

NumberTypes = Literal[
  "Byte",
  "Int8",
  "UInt16",
  "Int16",
  "UInt32",
  "Int32",
  "UInt64",
  "Int64",
  "Float32",
  "Float64",
  "CInt16",
  "CInt32",
  "CFloat32",
  "CFloat64",
]

CogCompression = Literal[
  "NONE",
  "LZW",
  "JPEG",
  "DEFLATE",
  "ZSTD",
  "WEBP",
  "LERC",
  "LERC_DEFLATE",
  "LERC_ZSTD",
  "LZMA",
]

CogOverviewCompression = Union[Literal["AUTO"], CogCompression]

CogResampling = Literal[
  "NEAREST", "AVERAGE", "BILINEAR", "CUBIC", "CUBICSPLINE", "LANCZOS", "MODE", "RMS"
]

WarpResampling = Union[CogResampling, Literal["RMS", "MIN", "MAX", "MED", "Q1", "Q3"]]


@dataclass
class GdalOptions:
  output_format: Optional[str] = None
  output_type: Optional[NumberTypes] = None
  outsize: Optional[tuple[Union[int, str], Union[int, str]]] = None
  resampling: Optional[ResampleAlgorithms] = None
  ovr: Optional[int] = None
  creation_options: Optional[dict[str, Any]] = None


@dataclass
class GdalTranslateOptions(GdalOptions):
  bands: Optional[Iterable[int]] = None
  scale: Optional[tuple[int, int]] = None
  scale_x: Optional[tuple[tuple[int, int], ...]] = None
  exponent: Optional[float] = None
  expand: Optional[Literal["gray", "rgb", "rgba"]] = None
  colorinterp: Optional[ColorInterp] = None
  colorinterp_x: Optional[tuple[ColorInterp, ...]] = None
  nogcp: Optional[bool] = None
  a_srs: Optional[str] = None
  a_ullr: Optional[tuple[int, ...]] = None
  a_gt: Optional[tuple[float, ...]] = None


@dataclass
class GdalWarpOptions(GdalOptions):
  tr: Optional[bool] = None
  tap: Optional[bool] = None
  tps: Optional[bool] = None
  rpc: Optional[bool] = None
  geoloc: Optional[bool] = None
  to: Optional[dict[str, Any]] = None


@dataclass
class GdalTransformOptions:
  s_srs: Optional[str] = None
  s_coord_epoch: Optional[int] = None
  t_srs: Optional[str] = None
  t_coord_epoch: Optional[int] = None
  ct: Optional[str] = None
  to: Optional[dict[str, str]] = None
  order: Optional[int] = None
  tps: bool = False
  rpc: bool = False
  geoloc: bool = False
  inverse: bool = False
  gcp: Optional[str] = None
  output_xy: bool = False
  ignore_extra_input: bool = False
  echo: bool = False
  field_sep: Optional[str] = None
  srcfile: Optional[str] = None
  dstfile: Optional[str] = None


class CogOptions(TypedDict, total=False):
  # https://gdal.org/en/stable/drivers/raster/cog.html
  blocksize: Optional[int]
  interleave: Optional[Literal["BAND", "PIXEL", "TILE"]]
  compress: Optional[CogCompression]
  level: Optional[int]
  max_z_error: Optional[int]
  max_z_error_overview: Optional[int]
  quality: Optional[int]
  jxl_lossless: Optional[Literal["YES", "NO"]]
  jxl_effort: Optional[int]
  jxl_distance: Optional[float]
  jxl_alpha_distance: Optional[float]
  num_threads: Optional[Union[int, Literal["ALL_CPUS"]]]
  nbits: Optional[int]
  predictor: Optional[Literal["YES", "NO", "STANDARD", "FLOATING_POINT"]]
  bigtiff: Optional[Literal["YES", "NO", "IF_NEEDED", "IF_SAFER"]]
  resampling: Optional[CogResampling]
  overview_resampling: Optional[CogResampling]
  warp_resampling: Optional[WarpResampling]
  overviews: Optional[Literal["AUTO", "IGNORE_EXISTING", "FORCE_USE_EXISTING", "NONE"]]
  overview_count: Optional[int]
  overview_compress: Optional[CogOverviewCompression]
  overview_quality: Optional[int]
  overview_predictor: Optional[Literal["YES", "NO", "STANDARD", "FLOATING_POINT"]]
  geotiff_version: Optional[Literal["AUTO", "1.0", "1.1"]]
  sparse_ok: Optional[Literal["TRUE", "FALSE"]]
  statistics: Optional[Literal["AUTO", "YES", "NO"]]


class BandMetadata(TypedDict):
  STATISTICS_MAXIMUM: str
  STATISTICS_MEAN: str
  STATISTICS_MINIMUM: str
  STATISTICS_STDDEV: str
  STATISTICS_VALID_PERCENT: str


class Band(TypedDict, total=False):
  band: int
  block: list[int]
  type: NumberTypes
  colorInterpretation: str
  min: float
  max: float
  minimum: float
  maximum: float
  mean: float
  stdDev: float
  metadata: dict[Literal[""], BandMetadata]


def gdalinfo(
  path: Path,
  min_max: bool = False,
  stats: Optional[Literal["exact", "approx"]] = None,
) -> dict:
  if not path.exists():
    raise FileNotFoundError(f"Invalid path: {str(path)}")

  gdalinfo_path = os.environ["GDAL_PATH"] + "/gdalinfo.exe"
  cmd = [gdalinfo_path, "-json"]

  if min_max:
    cmd += ["-mm"]

  if stats:
    cmd += ["-stats"] if stats == "exact" else ["-approx_stats"]

  cmd += [path]
  process = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")

  if process.returncode != 0:
    raise RuntimeError(f"gdalinfo failed:\n{process.stderr}")

  return json.loads(process.stdout)


def parse_gdalinfo_json_field(gdal_info: dict, field: str) -> Union[dict, None]:
  metadata_json = gdal_info.get("metadata", {}).get("", {}).get(field)

  if metadata_json is None:
    return None

  try:
    return json.loads(metadata_json)
  except json.JSONDecodeError as e:
    raise ValueError(f"Invalid json string: {e}")


def is_cloud_optimized(path: Path) -> bool:
  if not path.exists():
    raise FileNotFoundError(f"Invalid path: {str(path)}")

  gdal_python = os.environ["GDAL_PATH"] + "/python/validate_cloud_optimized_geotiff.py"
  python_exe = "python"

  process = subprocess.run(
    [python_exe, gdal_python, str(path)], capture_output=True, text=True
  )

  return process.returncode == 0


def gdal_translate(
  input_path: Path,
  output_path: Path,
  options: Optional[GdalTranslateOptions] = None,
  create_aux: bool = False,
):
  gdal_translate_path = os.environ["GDAL_PATH"] + "/gdal_translate.exe"

  cmd = [gdal_translate_path]

  if options is not None:
    if options.output_format is not None:
      cmd += ["-of", options.output_format]

    if options.output_type is not None:
      cmd += ["-ot", options.output_type]

    if options.ovr is not None:
      cmd += ["-ovr", str(options.ovr)]

    if options.resampling is not None:
      cmd += ["-r", options.resampling]

    if options.scale is not None:
      cmd += ["-scale"]
      if options.scale:
        cmd += [str(s) for s in options.scale]

    if options.scale_x is not None:
      for i, scale in enumerate(options.scale_x):
        cmd += [f"-scale_{i + 1}"]
        cmd += [str(s) for s in scale]

    if options.exponent is not None:
      cmd += ["-exponent", str(options.exponent)]

    if options.bands is not None:
      for b in options.bands:
        cmd += ["-b", str(b)]

    if options.outsize is not None:
      w, h = options.outsize
      cmd += ["-outsize", str(w), str(h)]

    if options.expand is not None:
      cmd += ["-expand", options.expand]

    if options.colorinterp is not None:
      cmd += ["-colorinterp", options.colorinterp]

    if options.colorinterp_x is not None:
      for band, interp in enumerate(options.colorinterp_x):
        cmd += [f"-colorinterp_{band + 1}", interp]

    if options.nogcp is not None:
      cmd += ["-nogcp"]

    if options.a_srs is not None:
      cmd += ["-a_srs", options.a_srs]

    if options.a_ullr is not None:
      cmd += ["-a_ullr"] + [str(i) for i in options.a_ullr]

    if options.a_gt is not None:
      cmd += ["-a_gt"] + [str(i) for i in options.a_gt]

    if options.creation_options is not None:
      for k, v in options.creation_options.items():
        cmd += ["-co", f"{k.upper()}={str(v)}"]

  if not create_aux:
    cmd += ["--config", "GDAL_PAM_ENABLED", "NO"]

  cmd += [str(input_path), str(output_path)]

  result = subprocess.run(cmd, capture_output=True, text=True)

  if result.returncode != 0:
    raise RuntimeError(
      f"gdal_translate failed for {input_path}\n"
      f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


def gdalwarp(
  input_path: Path,
  output_path: Path,
  options: Optional[GdalWarpOptions] = None,
  create_aux: bool = False,
):
  gdalwarp_path = os.environ["GDAL_PATH"] + "/gdalwarp.exe"

  cmd = [gdalwarp_path]

  if options is not None:
    if options.output_format is not None:
      cmd += ["-of", options.output_format]

    if options.outsize is not None:
      w, h = options.outsize
      cmd += ["-ts", str(w), str(h)]

    if options.tr is not None:
      cmd += ["-tr", "square"]

    if options.to is not None:
      for k, v in options.to.items():
        if v is None:
          continue

        cmd += ["-to", f"{k.upper()}={str(v).upper()}"]

    if options.output_type is not None:
      cmd += ["-ot", options.output_type]

    if options.ovr is not None:
      cmd += ["-ovr", str(options.ovr)]

    if options.resampling is not None:
      cmd += ["-r", options.resampling]

    if options.creation_options is not None:
      for k, v in options.creation_options.items():
        if v is None:
          continue

        cmd += ["-co", f"{k.upper()}={str(v).upper()}"]

  if not create_aux:
    cmd += ["--config", "GDAL_PAM_ENABLED", "NO"]

  cmd += [str(input_path), str(output_path)]

  result = subprocess.run(cmd, capture_output=True, text=True)

  if result.returncode != 0:
    raise RuntimeError(
      f"gdalwarp failed for {input_path}\n"
      f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


def gdaltransform(
  srcfile: str,
  dstfile: Optional[str] = None,
  options: Optional[GdalTransformOptions] = None,
):

  gdaltransform_path = os.environ["GDAL_PATH"] + "/gdaltransform.exe"

  cmd = [gdaltransform_path]

  if options is not None:
    if options.s_srs is not None:
      cmd += ["-s_srs", options.s_srs]

    if options.s_coord_epoch is not None:
      cmd += ["-s_coord_epoch", options.s_coord_epoch]

    if options.t_srs is not None:
      cmd += ["-t_srs", options.t_srs]

    if options.t_coord_epoch is not None:
      cmd += ["-t_coord_epoch", options.t_coord_epoch]

    if options.ct is not None:
      cmd += ["-ct", options.ct]

    if options.to is not None:
      for k, v in options.to.items():
        if v is None:
          continue

        cmd += ["-to", f"{k.upper()}={str(v).upper()}"]

    if options.order is not None:
      cmd += ["-order", options.order]

    if options.tps:
      cmd += ["-tps"]

    if options.rpc:
      cmd += ["-rpc"]

    if options.inverse:
      cmd += ["-i"]

    if options.gcp is not None:
      cmd += ["-gcp", options.gcp]

    if options.output_xy:
      cmd += ["-output_xy"]

    if options.ignore_extra_input:
      cmd += ["-ignore_extra_input"]

    if options.echo:
      cmd += ["-E"]

    if options.field_sep is not None:
      cmd += ["-field_sep", options.field_sep]

  cmd += [srcfile]

  if dstfile is not None:
    cmd += [dstfile]

  process = subprocess.run(cmd, capture_output=True, text=True)

  if process.returncode != 0:
    raise RuntimeError(
      f"gdaltransform failed for {cmd}\nSTDOUT: {process.stdout}\nSTDERR: {process.stderr}"
    )

  result = [
    tuple(map(float, line.split())) for line in process.stdout.strip().split("\n")
  ]
  return result


def corner_coordinates_from_geotransform(gdal_info: dict, wkt: bool = True):
  stac = gdal_info.get("stac")
  if stac is None:
    return None

  height, width = stac["proj:shape"]
  px_w, row_rot, x_origin, col_rot, px_h, y_origin = stac["proj:transform"]
  source_srs = stac["proj:epsg"]

  corners_utm = (
    (x_origin, y_origin),  # top left
    (x_origin + width * px_w, y_origin + width * col_rot),  # top right
    (x_origin + height * row_rot, y_origin + height * px_h),  # bottom left
    (
      x_origin + width * px_w + height * row_rot,
      y_origin + width * col_rot + height * px_h,
    ),  # bottom_right
  )

  srcfile = "\n".join(f"{x} {y}" for x, y in corners_utm)

  options = GdalTransformOptions(s_srs=f"EPSG:{source_srs}", t_srs="EPSG:4326")
  result = gdaltransform(srcfile, options=options)

  if not wkt:
    return result

  points = [f"{lon} {lat}" for lon, lat, _, _ in result]
  points.append(points[0])

  return f"POLYGON(({', '.join(points)}))"


def geotiff_to_thumbnail(
  input_path: Path, output_path: Path, thumbnail_size: tuple[int, int]
):
  temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
  temp_tif = Path(temp_file.name)
  temp_file.close()

  try:
    gdal_translate(
      input_path,
      temp_tif,
      GdalTranslateOptions(
        output_format="GTiff", a_ullr=(0, 118610, 10021, 0), a_srs="", nogcp=True
      ),
    )

    translate_options = GdalTranslateOptions(
      output_format="PNG", outsize=thumbnail_size
    )
    gdal_translate(temp_tif, output_path, translate_options, create_aux=False)

  finally:
    if temp_tif.exists():
      temp_tif.unlink()


def band_ranges(path: Path, z: int = 3, bound: bool = False) -> list[tuple[int, int]]:
  info = gdalinfo(path, stats="exact")

  bands = info.get("bands")
  if bands is None:
    raise RuntimeError(f"Invalid gdalinfo output: {json.dumps(info, indent=2)}")

  ranges: list[tuple[int, int]] = []
  for band in cast(list[Band], bands):
    metadata = band.get("metadata", {}).get("", {})
    mean = float(metadata.get("STATISTICS_MEAN", band["mean"]))
    std = float(metadata.get("STATISTICS_STDDEV", band["stdDev"]))

    zstd = z * std
    lower = mean - zstd
    upper = mean + zstd

    if bound:
      lower = max(lower, band["minimum"])
      upper = min(lower, band["maximum"])

    ranges.append((int(lower), int(upper)))

  return ranges
