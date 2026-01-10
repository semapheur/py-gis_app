from src.spatialite import DATETIME_FIELD, ColumnType, Field, Model, SpatialDatabase


class EquipmentListTable(Model):
  table_name = "equipment"
  id = Field(str, primary_key=True)
  identifier = Field(str, nullable=False)
  displayName = Field(str, nullable=False)
  description = Field(str)
  descriptionShort = Field(str)
  natoName = Field(str)
  nativeName = Field(str)
  alternativeNames = Field(str)
  source = Field(str)
  sourceData = Field(str)
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimeStamp = DATETIME_FIELD
  modifiedAtTimeStamp = DATETIME_FIELD
