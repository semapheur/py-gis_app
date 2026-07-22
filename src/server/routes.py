import uuid
from pathlib import Path
from typing import Any, Callable, TypedDict, TypeVar

from src.hashing import decode_sha256_from_b64
from src.index.catalog import (
  InsertCatalog,
  UpdateCatalog,
  get_catalog_edit_data,
  get_catalog_index_data,
  insert_catalog,
  update_catalog,
  validate_catalog_dir,
)
from src.index.images import ImageQuery, get_image_info, index_images, search_images
from src.index.radiometric import get_radiometric_parameters
from src.models.annotation_schema import (
  InsertSchema,
  UpdateSchema,
  get_schema_data,
  get_schema_data_options,
  insert_schema,
  update_schema,
)
from src.models.areas import (
  AreaDelete,
  AreaId,
  AreaUpdate,
  delete_areas,
  get_area,
  get_areas,
  update_area,
)
from src.models.attributes import (
  ATTRIBUTE_TABLES,
  InsertAttribute,
  UpdateAttribute,
  get_attribute_data,
  get_attribute_options,
  get_attribute_tables,
  insert_attribute,
  update_attribute,
)
from src.models.equipment_annotation import (
  AnnotationUpdate,
  ConvertAnnotation,
  GhostSearch,
  convert_annotation,
  delete_annotations,
  get_annotation_ghosts,
  get_annotations_by_image,
  update_annotations,
)
from src.models.equipment_list import get_equipment, search_equipment, update_equipment
from src.models.security import (
  InsertSecurity,
  UpdateSecurity,
  get_security_data,
  insert_sequrity,
  update_security,
)
from src.models.update import TableUpdate
from src.server.api import ApiError, ApiHandler, api


class Handler(ApiHandler):
  @api("GET", "/api/attribute-tables")
  def _get_attribute_tables(self):
    return {"tables": get_attribute_tables()}

  @api("GET", "/api/schema-data-options")
  def _get_schema_data_options(self):
    return {"options": get_schema_data_options()}

  @api("GET", "/api/get-equipment")
  def _get_equipment(self):
    return get_equipment()

  @api("GET", "/api/get-areas")
  def _get_areas(self):
    return get_areas()

  @api("GET", "/api/get-catalogs-index")
  def _get_catalogs_index(self):
    return {"catalogs": get_catalog_index_data()}

  @api("GET", "/api/get-catalogs-edit")
  def _get_catalogs_edit(self):
    return {"catalogs": get_catalog_edit_data()}

  @api("GET", "/api/get-annotations/{image_id}")
  def _get_annotations(self, image_id: str):
    image_hash = decode_sha256_from_b64(image_id)
    return get_annotations_by_image(image_hash)

  @api("GET", "/api/attribute-data/schema")
  def _get_schema_data(self):
    return {"data": get_schema_data()}

  @api("GET", "/api/attribute-data/{table}")
  def _get_attribute_data(self, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid GET endpoint")
    return {"data": get_attribute_data(table)}

  @api("GET", "/api/get-attributes/{table}")
  def _get_attributes(self, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid GET endpoint")
    return {"options": get_attribute_options(table)}

  @api("POST", "/api/search-images")
  def _post_query_images(self, payload: ImageQuery):
    return search_images(payload)

  @api("POST", "/api/image-info")
  def _post_image_info(self, payload: dict):
    image_hash = decode_sha256_from_b64(payload["id"])
    return get_image_info(image_hash)

  @api("POST", "/api/update-equipment")
  def _post_update_equipment(self, payload: TableUpdate):
    return update_equipment(payload)

  @api("POST", "/api/insert-attribute/schema")
  def _post_insert_schema(self, payload: InsertSchema):
    return {"inserted_row": insert_schema(payload)}

  @api("POST", "/api/insert-attribute/{table}")
  def _post_insert_attribute(self, payload: InsertAttribute, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid POST endpoint")
    return {"inserted_row": insert_attribute(table, payload)}

  @api("POST", "/api/update-attribute/schema")
  def _post_update_schema(self, payload: UpdateSchema):
    return update_schema(payload)

  @api("POST", "/api/update-attribute/{table}")
  def _post_update_attribute(self, payload: UpdateAttribute, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid POST endpoint")
    return update_attribute(table, payload)

  @api("POST", "/api/update-area")
  def _post_update_area(self, payload: AreaUpdate):
    name = update_area(payload)
    if name is not None:
      raise ApiError(409, f"Area with '{name}' already exist!")

  @api("POST", "/api/delete-areas")
  def _post_delete_areas(self, payload: AreaDelete):
    delete_areas(payload)

  @api("POST", "/api/validate-catalog-dir")
  def _post_validate_catalog_dir(self, payload: dict):
    input_path = Path(payload["path"])
    try:
      validate_catalog_dir(input_path)
    except FileNotFoundError as e:
      raise ApiError(400, str(e))
    except ValueError as e:
      raise ApiError(409, str(e))
    return {"valid": True}

  @api("POST", "/api/index-catalog", stream=True)
  def _post_index_catalog(self, payload: dict, send_event: Callable[[str, dict], None]):
    catalog_id = uuid.UUID(payload["id"])

    def on_progress(current: int, total: int, filename: str):
      send_event(
        "progress",
        {
          "current": current,
          "total": total,
          "filename": filename,
          "percent": round(current / total * 100) if total else 0,
        },
      )

    index_images(catalog_id, progress_callback=on_progress)

  @api("POST", "/api/radiometric-params")
  def _post_parametric_params(self, payload: dict[str, str]):
    hash = decode_sha256_from_b64(payload["id"])
    return get_radiometric_parameters(hash, ("noise", "sigma0"))
