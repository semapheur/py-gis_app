import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Optional, TypedDict, Union, cast

from src.env import load_env

load_env()

ResampleAlgorithms = Literal[
  "nearest", "bilinear", "cubic", "cubicspline", "lanczos", "average", "rms", "mode"
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


@dataclass
class GdalTranslateOptions:
  bands: Optional[Iterable[int]] = None
  output_type: Optional[NumberTypes] = None
  ovr: Optional[int] = None
  resampling: Optional[ResampleAlgorithms] = None
  scale: Optional[tuple[int, int]] = None
  scale_x: Optional[list[tuple[int, int]]] = None
  exponent: Optional[float] = None
  outsize: Optional[tuple[Union[int, str], Union[int, str]]] = None
  expand: Optional[Literal["gray", "rgb", "rgba"]] = None
  colorinterp: Optional[ColorInterp] = None
  colorinterp_x: Optional[tuple[ColorInterp, ...]] = None
  a_srs: Optional[str] = None
  a_ullr: Optional[list[int]] = None
  creation_options: Optional[dict[str, str]] = None


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


def gdal_translate(
  input_path: Path,
  output_path: Path,
  output_format: str,
  options: Optional[GdalTranslateOptions] = None,
  create_aux: bool = False,
):
  gdal_translate_path = os.environ["GDAL_PATH"] + "/gdal_translate.exe"

  cmd = [gdal_translate_path, "-of", output_format]

  if options is not None:
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

    if options.a_srs is not None:
      cmd += ["-a_srs", options.a_srs]

    if options.a_ullr is not None:
      cmd += ["-a_ullr"] + [str(i) for i in options.a_ullr]

    if options.creation_options is not None:
      for k, v in options.creation_options.items():
        cmd += ["-co", f"{k}={v}"]

  if not create_aux:
    cmd += ["--config", "GDAL_PAM_ENABLED", "NO"]

  cmd += [str(input_path), str(output_path)]

  result = subprocess.run(cmd, capture_output=True, text=True)

  if result.returncode != 0:
    raise RuntimeError(
      f"gdal_translate failed for {input_path}\n"
      f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )


class BandMetadata(TypedDict):
  STATISTICS_MAXIMUM: str
  STATISTICS_MEAN: str
  STATISTICS_MINIMUM: str
  STATISTICS_STDDEV: str
  STATISTICS_VALID_PERCENT: str


class Band(TypedDict):
  band: int
  block: list[int]
  colorInterpretation: str
  maximum: float
  mean: float
  metadata: dict[Literal[""], BandMetadata]
  minimum: float
  stdDev: float
  type: NumberTypes


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
