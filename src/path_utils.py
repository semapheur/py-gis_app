from pathlib import Path


def verify_dir(path: Path):
  if not path.is_dir():
    raise FileNotFoundError(f"Invalid directory path: {path}")
