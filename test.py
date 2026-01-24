from pathlib import Path

from src.annotations.models import create_annotation_tables
from src.attributes.models import create_attribute_tables
from src.index.catalog import add_calatog
from src.index.images import index_images

if __name__ == "__main__":
  create_annotation_tables()
  # create_attribute_tables()

  # catalog_path = Path("C:/Users/danfy/Documents/Projects/py-gis_app/data")
  # add_calatog(catalog_path, "test")
#
# index_images(1)
