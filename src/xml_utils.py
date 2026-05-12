import xml.etree.ElementTree as ET
from typing import Union


def _float(element: ET.Element, tag: str) -> float:
  value = element.findtext(tag)
  if value is None:
    raise ValueError(f"Missing required tag: {tag}")

  return float(value)


def _int(element: ET.Element, tag: str) -> int:
  value = element.findtext(tag)
  if value is None:
    raise ValueError(f"Missing required tag: {tag}")

  return int(value)


def xml_to_dict(element: ET.Element) -> Union[dict, str]:
  children = list(element)

  if not children:
    text = (element.text or "").strip()

    try:
      return int(text)
    except ValueError:
      pass

    try:
      return float(text)
    except ValueError:
      pass

    parts = text.split()
    if len(parts) > 1:
      try:
        return [float(p) for p in parts]
      except ValueError:
        pass

    return text

  result = {}
  for child in children:
    value = xml_to_dict(child)
    if child.tag in result:
      if not isinstance(result[child.tag], list):
        result[child.tag] = [result[child.tag]]

      result[child.tag].append(value)

    else:
      result[child.tag] = value

  return result
