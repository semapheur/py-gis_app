import inspect
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def move_contents(from_dir: Path, to_dir: Path):
  to_dir.mkdir(parents=True, exist_ok=True)

  for item in from_dir.iterdir():
    shutil.move(str(item), str(to_dir / item.name))


def copy_contents(from_dir: Path, to_dir: Path):
  to_dir.mkdir(parents=True, exist_ok=True)

  for item in from_dir.iterdir():
    target = to_dir / item.name
    if item.is_dir():
      shutil.copytree(item, target, dirs_exist_ok=True)
    else:
      shutil.copy2(item, target)


def append_file_suffix(root: Path, target_suffixes: Sequence[str], extra_suffix: str):
  suffix_set = {s.lower() for s in target_suffixes}

  for file in root.rglob("*"):
    if not file.is_file():
      continue

    if file.suffix.lower() not in suffix_set:
      continue

    new_name = file.with_name(file.name + extra_suffix)
    file.rename(new_name)


def remove_extra_suffix(root: Path, extra_suffix: str):
  for file in root.rglob("*"):
    if not file.is_file():
      continue

    file_suffixes = file.suffixes
    if len(file_suffixes) > 1 and file_suffixes[-1] == extra_suffix:
      new_name = file.name[: -len(extra_suffix)]
      file.rename(file.with_name(new_name))


def create_dist_structure(base: Path = Path("dist")):
  dirs = (
    base / "static" / "cog",
    base / "static" / "thumbnails",
    base / "db",
  )

  for d in dirs:
    d.mkdir(parents=True, exist_ok=True)


def detect_node_package_manager(project_dir: Path):
  if (project_dir / "pnpm-lock.yaml").exists():
    return "pnpm"
  if (project_dir / "yarn.lock").exists():
    return "yarn"
  if (project_dir / "package-lock.json").exists():
    return "npm"

  raise ValueError(f"No lockfile detected in: {str(project_dir)}")


def build_frontend():
  frontend_dir = Path("frontend")
  package_manager = detect_node_package_manager(frontend_dir)
  subprocess.run([package_manager, "build"], cwd=frontend_dir, check=True, shell=True)


def package_app(zip_dist: bool = False, mask_suffixes: bool = False):
  create_dist_structure()
  build_frontend()
  move_contents(Path("frontend/build"), Path("dist/static"))
  shutil.copytree(
    "src",
    "dist/src",
    dirs_exist_ok=True,
    ignore=shutil.ignore_patterns("__pycache__"),
  )
  shutil.copy2("app.py", "dist/app.py")
  shutil.copy2(".env", "dist/.env")

  if mask_suffixes:
    append_file_suffix(Path("dist"), (".js", ".py"), ".txt")

    function_source = inspect.getsource(remove_extra_suffix)
    with open("dist/restore_filenames.py.txt", "w") as f:
      f.write(function_source)

  if zip_dist:
    shutil.make_archive("dist", "zip", root_dir="dist")


if __name__ == "__main__":
  package_app(True, True)
