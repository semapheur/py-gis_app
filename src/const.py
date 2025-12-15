import os
from pathlib import Path

from src.env import load_env

load_env()

STATIC_DIR = Path(os.environ["STATIC_DIR"])
INDEX_DB = Path(os.environ["DB_DIR"]) / "index.db"
