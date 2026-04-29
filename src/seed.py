from src.index.catalog import create_catalog_table
from src.index.images import create_index_table
from src.index.radiometric import create_radiometric_table
from src.models.annotation import create_annotation_tables
from src.models.areas import create_areas_tables
from src.models.attributes import create_attribute_tables
from src.models.equipment import create_equipment_table


def create_db_tables():
  create_catalog_table()
  create_index_table()
  create_radiometric_table()
  create_annotation_tables()
  create_areas_tables()
  create_attribute_tables()
  create_equipment_table()
