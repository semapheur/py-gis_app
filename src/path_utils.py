from pathlib import Path


def verify_dir(path: Path):
  if not path.is_dir():
    raise FileNotFoundError(f"Invalid directory path: {path}")


def build_tree(root: Path, prefix="") -> list[str]:
  lines = [str(root)]

  def walk(path: Path, prefix=""):
    entries = sorted(path.iterdir(), key=lambda p: p.name)

    for i, entry in enumerate(entries):
      connector = "└── " if i == len(entries) - 1 else "├── "
      lines.append(prefix + connector + entry.name)

      if entry.is_dir():
        extensions = "    " if i == len(entries) - 1 else "│   "
        walk(entry, prefix + extensions)

  walk(root)
  return lines
