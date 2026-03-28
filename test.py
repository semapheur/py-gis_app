import os
import sqlite3

from src.env import add_to_path, load_env

if __name__ == "__main__":
  load_env()

  test = "C:/Program Files/QGIS 4.0.0/bin/mod_spatialite"

  print(os.path.dirname(test))

  # conn = sqlite3.connect(":memory:")
  # conn.enable_load_extension(True)
  # conn.load_extension(r"C:\Program Files\QGIS 4.0.0\bin\mod_spatialite")
