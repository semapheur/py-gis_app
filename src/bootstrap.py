import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.env import add_to_path, load_env, require_env


@dataclass(frozen=True)
class Settings:
  DB_DIR: Path
  STATIC_DIR: Path
  SPATIALITE_PATH: Path
  HOST: str
  PORT: int

  @property
  def ANNOTATION_DB(self) -> Path:
    return self.DB_DIR / "annotation.db"

  @property
  def ATTRIBUTE_DB(self) -> Path:
    return self.DB_DIR / "attribute.db"

  @property
  def EQUIPMENT_DB(self) -> Path:
    return self.DB_DIR / "equipment.db"

  @property
  def INDEX_DB(self) -> Path:
    return self.DB_DIR / "index.db"

  @property
  def LOCATION_DB(self) -> Path:
    return self.DB_DIR / "location.db"

  @property
  def LOG_DB(self) -> Path:
    return self.DB_DIR / "log.db"


def load_settings() -> Settings:
  return Settings(
    DB_DIR=Path(require_env("DB_DIR")),
    STATIC_DIR=Path(require_env("STATIC_DIR")),
    SPATIALITE_PATH=Path(require_env("SPATIALITE")),
    HOST=os.getenv("HOST", "0.0.0.0"),
    PORT=int(os.getenv("PORT", "8080")),
  )


@lru_cache
def get_settings():
  load_env()

  settings = load_settings()

  spatialite_dir = settings.SPATIALITE_PATH.parent
  add_to_path(spatialite_dir)

  return settings
