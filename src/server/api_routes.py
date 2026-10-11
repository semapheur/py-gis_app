import uuid
from pathlib import Path
from typing import Callable

from src.hashing import decode_sha256_from_b64
from src.index.catalog import (
  CatalogInsert,
  CatalogUpdate,
  get_catalog_edit_data,
  get_catalog_index_data,
  insert_catalog,
  update_catalog,
  validate_catalog_dir,
)
from src.index.images import ImageQuery, get_image_info, index_images, search_images
from src.index.radiometric import get_radiometric_parameters
from src.models.annotation_attributes import (
  ANNOTATION_ATTRIBUTE_TABLES,
  AttributeInsert,
  AttributeUpdate,
  get_attribute_options,
  insert_attribute,
  update_attribute,
)
from src.models.annotation_commit import (
  delete_annotations,
  get_annotations_by_image,
  update_annotations,
)
from src.models.annotation_schema import (
  SchemaInsert,
  SchemaUpdate,
  get_schema_data,
  get_schema_data_options,
  get_schema_options,
  insert_schema,
  update_schema,
)
from src.models.areas import (
  AreaDelete,
  AreaUpdate,
  delete_areas,
  get_area,
  get_areas,
  get_areas_by_image,
  update_area,
)
from src.models.attributes import ATTRIBUTE_TABLE_GETTER, get_attribute_data
from src.models.equipment_annotation import (
  AnnotationConvert,
  AnnotationUpdate,
  GhostSearch,
  convert_annotation,
  get_annotation_ghosts,
)
from src.models.equipment_list import (
  InsertEquipment,
  UpdateEquipment,
  get_equipment,
  insert_equipment,
  search_equipment,
  update_equipment,
)
from src.models.security import (
  SECURITY_TABLES,
  SecurityInsert,
  SecurityUpdate,
  insert_sequrity,
  update_security,
)
from src.server.api_handler import ApiError, ApiHandler, api


def static_get(path: str, key: str | None, fn: Callable[[], Any]) -> Callable:
  def handler(self):
    result = fn()
    return {key: result} if key else result

  return api("GET", path)(handler)


class ApiRoutes(ApiHandler):
  @api("GET", "/api/attribute-tables")
  def _get_attribute_tables(self):
    attribute_type = self.require_choice(
      "type", ATTRIBUTE_TABLE_GETTER, "attribute type"
    )
    return {"tables": ATTRIBUTE_TABLE_GETTER[attribute_type]()}

  @api("GET", "/api/schema-options")
  def _get_schema_options(self):
    return {"options": get_schema_options()}

  @api("GET", "/api/schema-data-options")
  def _get_schema_data_options(self):
    return {"options": get_schema_data_options()}

  @api("GET", "/api/get-equipment")
  def _get_equipment(self):
    return {"equipment": get_equipment()}

  @api("GET", "/api/get-areas")
  def _get_areas(self):
    return get_areas()

  @api("GET", "/api/get-areas-by-image")
  def _post_get_areas(self):
    return get_areas_by_image(self.require_image_hash())

  @api("GET", "/api/get-catalogs-index")
  def _get_catalogs_index(self):
    return {"catalogs": get_catalog_index_data()}

  @api("GET", "/api/get-catalogs-edit")
  def _get_catalogs_edit(self):
    return {"catalogs": get_catalog_edit_data()}

  @api("GET", "/api/get-annotations-by-image")
  def _get_annotations(self):
    return get_annotations_by_image(self.require_image_hash())

  @api("GET", "/api/attribute-data/schema")
  def _get_schema_data(self):
    return {"data": get_schema_data()}

  @api("GET", "/api/attribute-data")
  def _get_attribute_data(self):
    table = self.require_param("table", "attribute table")

    try:
      return {"data": get_attribute_data(table)}
    except ValueError as e:
      raise ApiError(400, str(e)) from e

  @api("GET", "/api/get-attributes")
  def _get_attributes(self):
    table = self.require_choice(
      "table", ANNOTATION_ATTRIBUTE_TABLES, "annotation attribute table"
    )
    return {"options": get_attribute_options(table)}

  @api("POST", "/api/search-images")
  def _post_query_images(self, payload: ImageQuery):
    return search_images(payload)

  @api("GET", "/api/image-info")
  def _post_image_info(self):
    return get_image_info(self.require_image_hash())

  @api("POST", "/api/insert-attribute/schema")
  def _post_insert_schema(self, payload: SchemaInsert):
    return {"inserted_row": insert_schema(payload)}

  @api("POST", "/api/insert-attribute/{table}")
  def _post_insert_attribute(self, payload: AttributeInsert, table: str):
    if table not in ANNOTATION_ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid POST endpoint")
    return {"inserted_row": insert_attribute(table, payload)}

  @api("POST", "/api/update-attribute/schema")
  def _post_update_schema(self, payload: SchemaUpdate):
    return update_schema(payload)

  @api("POST", "/api/update-attribute/{table}")
  def _post_update_attribute(self, payload: AttributeUpdate, table: str):
    if table not in ANNOTATION_ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid POST endpoint")
    return update_attribute(table, payload)

  @api("POST", "/api/insert-security/{table}")
  def _post_insert_security(self, payload: SecurityInsert, table: str):
    if table not in SECURITY_TABLES:
      raise ApiError(404, "Invalid POST endpoint")

    inserted_row = insert_sequrity(table, payload)
    return {"inserted_row": inserted_row}

  @api("POST", "/api/update-security/{table}")
  def _post_update_security(self, payload: SecurityUpdate, table: str):
    if not table or table not in SECURITY_TABLES:
      raise ApiError(404, "Invalid POST endpoint")

    return update_security(table, payload)

  @api("GET", "/api/search-equipment")
  def _get_search_equipment(self):
    query = self.require_param("query", "search query")
    return search_equipment(query)

  @api("POST", "/api/insert-equipment")
  def _post_insert_equipment(self, payload: InsertEquipment):
    return insert_equipment(payload)

  @api("POST", "/api/update-equipment")
  def _post_update_equipment(self, payload: UpdateEquipment):
    return update_equipment(payload)

  @api("GET", "/api/get-area")
  def _get_fetch_area(self):
    area_id = self.require_param("id", "area id")
    return get_area(area_id)

  @api("POST", "/api/update-area")
  def _post_update_area(self, payload: AreaUpdate):
    name = update_area(payload)
    if name is not None:
      raise ApiError(409, f"Area with '{name}' already exist!")

  @api("POST", "/api/delete-areas")
  def _post_delete_areas(self, payload: AreaDelete):
    delete_areas(payload)

  @api("POST", "/api/update-annotations")
  def _post_update_annotations(self, payload: list[AnnotationUpdate]):
    update_annotations(payload)
    return {"message": "Successfully updated annotations"}

  @api("POST", "/api/delete-annotations")
  def _post_delete_annotations(self, payload: dict[str, list[str]]):
    delete_annotations(payload)
    return {"message": "successfully deleted annotations"}

  @api("POST", "/api/convert-annotation")
  def _post_convert_annotation(self, payload: AnnotationConvert):
    convert_annotation(payload)
    return {"message": "Successfully converted annotation"}

  @api("POST", "/api/get-annotation-ghosts")
  def _post_fetch_annotation_ghosts(self, payload: GhostSearch):
    return get_annotation_ghosts(payload)

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

  @api("POST", "/api/insert-catalog")
  def _post_insert_catalog(self, payload: CatalogInsert):
    result = insert_catalog(payload)
    return {"inserted_row": result}

  @api("POST", "/api/update-catalog")
  def _post_update_catalog(self, payload: CatalogUpdate):
    result = update_catalog(payload)
    return {"updated_row": result}

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
