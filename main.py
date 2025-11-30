import json
import os
import sqlite3
from pathlib import Path
from pprint import pprint

from src.env import load_env
from src.imagery_index import index_images

load_env()


def spatialite(db_path: str):
  db = sqlite3.connect(db_path)
  db.enable_load_extension(True)
  db.load_extension(os.environ["SPATIALITE"])

  cursor = db.cursor()
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS cities (
      id INTEGER PRIMARY KEY,
      name TEXT
    )
  """)

  cursor.execute("SELECT AddGeometryColumn('cities', 'geometry', 4326, 'POINT', 'XY')")
  cursor.execute(
    "INSERT INTO cities (name, geometry) VALUES (?, GeomFromText(?, 4326))",
    ("New York", "POINT(10.75 59.91)"),
  )
  db.commit()

  cursor.execute("SELECT * FROM cities")
  print(cursor.fetchall())

  db.close()


if __name__ == "__main__":
  image_folder = Path("data")
  index_images(image_folder)

  # with open("test.js", "w") as f:
  #  json.dump(test, f, indent=2)
  # pprint(test)
