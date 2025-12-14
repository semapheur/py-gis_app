import base64
import hashlib
from pathlib import Path


def encode_sha256_to_b64(decoded: bytes) -> str:
  return base64.urlsafe_b64encode(decoded).decode("utf-8").rstrip("=")


def decode_sha256_from_b64(encoded: str) -> bytes:
  padding = "=" * (-len(encoded) % 4)
  return base64.urlsafe_b64decode(encoded + padding)


def hash_geotiff(image_path: Path) -> bytes:
  hasher = hashlib.sha256()

  with open(image_path, "rb") as f:
    for chunk in iter(lambda: f.read(8192), b""):
      hasher.update(chunk)

  return hasher.digest()
