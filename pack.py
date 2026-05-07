import shutil
import subprocess
from pathlib import Path


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


def package_app():
  create_dist_structure()
  build_frontend()
  move_contents(Path("frontend/build"), Path("dist/static"))
  shutil.copytree("src", "dist/src", dirs_exist_ok=True)
  shutil.copy2("app.py", "dist/app.py")
  shutil.copy2(".env", "dist/.env")


if __name__ == "__main__":
  package_app()
