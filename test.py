import sqlite3
import uuid
from pathlib import Path

from src.const import ANNOTATION_DB, ATTRIBUTE_DB
from src.hashing import decode_sha256_from_b64, encode_sha256_to_b64, uuid_bytes_to_str
from src.index.catalog import add_calatog
from src.index.images import index_images
from src.models.annotation import create_annotation_tables
from src.models.areas import create_areas_tables
from src.models.attributes import create_attribute_tables
from src.spatialite import SqliteDatabase

if __name__ == "__main__":
  create_areas_tables()
  # create_attribute_tables()

  # catalog_path = Path("C:/Users/danfy/Documents/Projects/py-gis_app/data")
  # add_calatog(catalog_path, "test")
#
# index_images(1)
