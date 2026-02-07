import os
from pathlib import Path

from src.env import load_env

load_env()

DB_DIR = Path(os.environ["DB_DIR"])
STATIC_DIR = Path(os.environ["STATIC_DIR"])
INDEX_DB = DB_DIR / "index.db"
ATTRIBUTE_DB = DB_DIR / "attribute.db"
ANNOTATION_DB = DB_DIR / "annotation.db"
LOCATION_DB = DB_DIR / "location.db"
