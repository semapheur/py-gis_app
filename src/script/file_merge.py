#!/usr/bin/env python3.14
"""Merge parts created by file_split.py back into the original file.

The original file does not need to exist. SOURCE can be any of:
  * a directory containing the parts (must hold exactly one set of parts)
  * any one part file, e.g. page.html.part03
  * the original path, e.g. page.html (only its name is used; the file need not exist)

Usage: file_merge.py SOURCE [-o OUTPUT] [--delete] [--force]
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

PART_RE = re.compile(r"^(?P<base>.+)\.part(?P<idx>\d+)$")


def group_parts(directory: Path) -> dict[str, list[tuple[int, Path]]]:
  groups: dict[str, list[tuple[int, Path]]] = {}
  for p in directory.iterdir():
    m = PART_RE.match(p.name)
    if m and p.is_file():
      groups.setdefault(m["base"], []).append((int(m["idx"]), p))
  return groups


def resolve(source: Path) -> tuple[Path, list[tuple[int, Path]]]:
  """Return (original path, unsorted [(index, part path)])."""
  if source.is_dir():
    groups = group_parts(source)
    if not groups:
      raise FileNotFoundError(f"no parts found in {source}")
    if len(groups) > 1:
      names = ", ".join(sorted(groups))
      raise ValueError(
        f"several sets of parts in {source}: {names}; pass one part file or the original name"
      )
    ((base, parts),) = groups.items()
    return source / base, parts

  m = PART_RE.match(source.name)
  if source.is_file() and m:  # a part file was given
    base = source.with_name(m["base"])
  else:  # original name (file may not exist)
    base = source
  parts = (
    group_parts(base.parent or Path(".")).get(base.name)
    if base.parent.is_dir()
    else None
  )
  if not parts:
    raise FileNotFoundError(f"no parts found for {base.name} in {base.parent}")
  return base, parts


def ordered_paths(parts: list[tuple[int, Path]]) -> list[Path]:
  if len({len(p.name) for _, p in parts}) != 1:
    raise ValueError(
      "inconsistent zero-padding among parts (stale parts from another split?)"
    )
  parts = sorted(parts, key=lambda t: t[0])
  indices = [i for i, _ in parts]
  if indices != list(range(len(parts))):
    missing = sorted(set(range(indices[-1] + 1)) - set(indices))
    raise ValueError(f"parts are not contiguous from 0; missing indices: {missing}")
  return [p for _, p in parts]


def main() -> int:
  ap = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
  )
  ap.add_argument(
    "source",
    type=Path,
    help="directory of parts, any one part file, or the original path",
  )
  ap.add_argument(
    "-o",
    "--output",
    type=Path,
    help="output file (default: original name, next to the parts)",
  )
  ap.add_argument(
    "--delete", action="store_true", help="delete the parts after a successful merge"
  )
  ap.add_argument(
    "--force", action="store_true", help="overwrite the output file if it exists"
  )
  args = ap.parse_args()

  try:
    original, raw_parts = resolve(args.source)
    parts = ordered_paths(raw_parts)
    output = args.output or original
    if output.exists() and not args.force:
      print(f"error: {output} exists (use --force to overwrite)", file=sys.stderr)
      return 1
    tmp = output.with_name(output.name + ".tmp")
    with tmp.open("wb") as fout:
      for p in parts:
        with p.open("rb") as fin:
          shutil.copyfileobj(fin, fout, 1 << 20)
    os.replace(tmp, output)
  except (OSError, ValueError) as e:
    print(f"error: {e}", file=sys.stderr)
    return 1

  if args.delete:
    for p in parts:
      p.unlink()
  print(f"merged {len(parts)} part(s) into {output}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
