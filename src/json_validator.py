import json
from dataclasses import dataclass, fields, MISSING
from typing import Any, Optional, Union, TypedDict, get_args, get_origin, get_type_hints, TYPE_CHECKING, cast
from typing_extensions import dataclass_transform

class ErrorMessage(TypedDict):
  field: str
  error: str

class ValidationError(Exception):
  def __init__(self, errors: list[ErrorMessage]):
    self.errors = errors
    super().__init__(json.dumps(errors, indent=2))

@dataclass_transform()
class BaseModel:
  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    dataclass(cls)

  def __post_init__(self):
    self._validate()

  def _validate(self):
    errors = []
    hints = get_type_hints(self.__class__)

    for field in fields(self):
      value = getattr(self, field.name)
      expected_type = hints.get(field.name)

      error = self._check_type(field.name, value, expected_type)
      if error:
        errors.append(error)

    if errors:
      raise ValidationError(errors)

  def _check_type(self, name: str, value: Any, expected_type: Any) -> Optional[ErrorMessage]:
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin is Union:
      if value is None and type(None) in args:
        return None

      non_none = [a for a in args if a is not type(None)]
      for t in non_none:
        if self._check_type(name, value, t) is None:
          return None

      return ErrorMessage(
        field=name,
        error= f"expected {expected_type}, got {type(value).__name__}")

    if origin is list:
      if not isinstance(value, list):
        return ErrorMessage(field=name, error=f"expected list, got {type(value).__name__}"}
      if args:
        for i, item in enumerate(value):
          if not isinstance(item, args[0]):
            return ErrorMessage(
              field= name,
              error= f"item [{i}] expected {args[0].__name__}, got {type(item).__name__}",
            )

      return None

    if origin is dict:
      if not isinstance(value, dict):
        return {"field": name, "error": f"expected dict, got {type(value).__name__}"}

      return None

    if expected_type and not isinstance(value, expected_type):
      return ErrorMessage(field=name, error=f"expected {expected_type.__name__}, got {type(value).__name__}")

  @classmethod
  def from_json(cls, raw: Union[str, bytes, dict]):
    if isinstance(raw, (str, bytes)):
      try:
        data = json.loads(raw)
      except json.JSONDecodeError as e:
        raise ValidationError([ErrorMessage(field="__root__", error=f"Invalid JSON: {e}")])

    else:
      data = raw

      field_names = {f.name for f in fields(cls)}
      kwargs = {k: v for k, v in data.items() if k in field_names}

      missing: list[ErrorMessage] = []
      for f in fields(cls):
        if f.name not in data and f.default is f.default_factory is MISSING:
          missing.append(ErrorMessage(field=f.name, error="required field missing"))

      if missing:
        raise ValidationError(missing)

      return cls(**kwargs)

  def to_dict(self) -> dict:
    return {f.name: getattr(self, f.name) for f in fields(self)}

  def to_json(self) -> str:
    return json.dumps(self.to_dict())
