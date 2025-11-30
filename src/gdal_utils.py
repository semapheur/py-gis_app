import json
import subprocess
from pathlib import Path


def gdalinfo(path: Path) -> dict:
  if not path.exists():
    raise FileNotFoundError(f"Invalid path: {str(path)}")

  gdalinfo_cmd = "C:/Program Files/QGIS 3.44.4/bin/gdalinfo.exe"

  process = subprocess.run(
    [gdalinfo_cmd, "-json", path], capture_output=True, text=True, errors="ignore"
  )

  if process.returncode != 0:
    raise RuntimeError(f"gdalinfo failed:\n{process.stderr}")

  return json.loads(process.stdout)
