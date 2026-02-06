import os
from pathlib import Path

from src.env import load_env

load_env()

db_dir = Path(os.environ["DB_DIR"])
STATIC_DIR = Path(os.environ["STATIC_DIR"])
INDEX_DB = db_dir / "index.db"
ATTRIBUTE_DB = db_dir / "attribute.db"
ANNOTATION_DB = db_dir / "annotation.db"
LOCATION_DB = db_dir / "locations.db"
