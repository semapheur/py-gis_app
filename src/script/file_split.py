#!/usr/bin/env python3.14
"""Split a large file into parts of at most N bytes (tag integrity is NOT preserved).

Parts are named "<name>.part<index>", 0-based, zero-padded to the fewest digits
that can represent the highest index (e.g. 10 parts -> part0..part9, 11 parts -> part00..part10).

Usage: file_split.py INPUT MAX_BYTES [-o OUTPUT_DIR]
MAX_BYTES accepts a plain integer or a K/M/G suffix (powers of 1024), e.g. 500K, 2M.
"""

import argparse
import sys
from pathlib import Path

BLOCK = 1 << 20  # copy in 1 MiB blocks so memory use stays small


def parse_size(text: str) -> int:
  units = {"k": 1 << 10, "m": 1 << 20, "g": 1 << 30}
  t = text.strip().lower().removesuffix("b").removesuffix("i")
  mult = units.get(t[-1:], 1)
  if t[-1:] in units:
    t = t[:-1]
  try:
    value = int(t) * mult
  except ValueError:
    raise argparse.ArgumentTypeError(f"invalid size: {text!r}") from None
  if value < 1:
    raise argparse.ArgumentTypeError("max size must be at least 1 byte")
  return value


def split_file(src: Path, max_bytes: int, out_dir: Path) -> list[Path]:
  total = src.stat().st_size
  if total == 0:
    raise ValueError("input file is empty")

  count = -(-total // max_bytes)  # ceiling division
  width = len(str(count - 1))  # fewest digits for indices 0..count-1
  out_dir.mkdir(parents=True, exist_ok=True)

  paths: list[Path] = []
  with src.open("rb") as fin:
    for i in range(count):
      part = out_dir / f"{src.name}.part{i:0{width}d}"
      remaining = max_bytes
      with part.open("wb") as fout:
        while remaining > 0:
          data = fin.read(min(BLOCK, remaining))
          if not data:
            break
          fout.write(data)
          remaining -= len(data)
      paths.append(part)
  return paths


def main() -> int:
  ap = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
  )
  ap.add_argument("input", type=Path, help="file to split")
  ap.add_argument(
    "max_bytes", type=parse_size, help="maximum size of each part in bytes"
  )
  ap.add_argument(
    "-o", "--out-dir", type=Path, help="output directory (default: same as input)"
  )
  args = ap.parse_args()

  if not args.input.is_file():
    ap.error(f"not a file: {args.input}")
  out_dir = args.out_dir or args.input.parent

  try:
    parts = split_file(args.input, args.max_bytes, out_dir)
  except (OSError, ValueError) as e:
    print(f"error: {e}", file=sys.stderr)
    return 1
  print(f"wrote {len(parts)} part(s): {parts[0].name} ... {parts[-1].name}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
