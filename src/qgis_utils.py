import os
import subprocess
from pathlib import Path

from src.env import load_env

load_env()


def qgis_raster_calculator(input_path: Path, output_path: Path, expression: str):
  qgis_process = os.environ["QGIS_PATH"] + "/qgis_process.exe"

  cmd = [
    qgis_process,
    "run",
    "native:rastercalc",
    "--distance_units=meters",
    "--area_units=m2",
    f"--LAYERS={input_path}",
    f"--EXPRESSION={expression}",
    f"--OUTPUT={output_path}",
  ]

  result = subprocess.run(cmd, capture_output=True, text=True)
  if result.returncode != 0:
    raise RuntimeError(
      f"qgis_process failed for {input_path}\n"
      f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
