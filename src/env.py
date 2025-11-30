import os


def load_env(path=".env", override=False):
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
