from src.index.catalog import create_catalog_table
from src.index.images import create_index_table
from src.index.radiometric import create_radiometric_table
from src.models.annotation_attributes import create_annotation_attribute_tables
from src.models.annotation_commit import create_annotation_tables
from src.models.annotation_schema import create_schema_table
from src.models.areas import create_areas_tables
from src.models.equipment_list import create_equipment_table
from src.models.references import create_reference_tables
from src.models.security import create_security_tables


def create_db_tables():
  create_catalog_table()
  create_index_table()
  create_radiometric_table()
  create_schema_table()
  create_annotation_tables()
  create_areas_tables()
  create_annotation_attribute_tables()
  create_security_tables()
  create_reference_tables()
  create_equipment_table()
