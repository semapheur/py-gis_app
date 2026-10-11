from src.models.annotation_attributes import (
  ANNOTATION_ATTRIBUTE_TABLES,
  get_annotation_attribute_data,
  get_annotation_attribute_tables,
)
from src.models.references import (
  REFERENCE_ATTRIBUTE_TABLES,
  Originator,
  get_reference_attribute_data,
  get_reference_attribute_tables,
)
from src.models.security import (
  SECURITY_TABLES,
  get_security_attribute_tables,
  get_security_data,
)

ATTRIBUTE_TABLE_GETTER = {
  "annotation": get_annotation_attribute_tables,
  "reference": get_reference_attribute_tables,
  "security": get_security_attribute_tables,
}


def get_attribute_data(table: str):
  if table in ANNOTATION_ATTRIBUTE_TABLES:
    return get_annotation_attribute_data(table)

  elif table in SECURITY_TABLES:
    return get_security_data(table)

  elif table in (Originator._table_name,) + tuple(REFERENCE_ATTRIBUTE_TABLES):
    return get_reference_attribute_data(table)

  raise ValueError(f"Invalid attribute table: {table}")
