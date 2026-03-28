import os
from pathlib import Path


def load_env(path: str = ".env", override: bool = False):
  if not os.path.exists(path):
    raise FileNotFoundError(f"{path} not found")

  with open(path, "r") as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#"):
        continue

      if "=" not in line:
        continue
      key, value = line.split("=", 1)

      # Clean up whitespace and quotes
      key = key.strip()
      value = value.strip().strip('"').strip("'")

      # Only set if not already present, unless override=True
      if override or key not in os.environ:
        os.environ[key] = value


def require_env(name: str) -> str:
  value = os.getenv(name)

  if value is None:
    raise RutimeError(f"Missing required environment variable: {name}")

  return value


def add_to_path(new_dir: Path, prepend: bool = False):
  new_dir = new_dir.resolve()

  if not new_dir.is_dir():
    raise ValueError(
      f"Failed to add PATH variable: {new_dir} is not a valid directory."
    )

  current_path = os.environ.get("PATH", "")
  parts = [os.path.normpath(p) for p in current_path.split(os.pathsep) if p]

  if new_dir not in parts:
    if prepend:
      parts.insert(0, new_dir)
    else:
      parts.append(new_dir)

    os.environ["PATH"] = os.pathsep.join(str(p) for p in parts)
