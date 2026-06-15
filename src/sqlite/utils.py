from typing import Union


def uuid_blob_to_str(blob: bytes) -> Union[str, None]:
  if blob is None:
    return None

  hexstr = blob.hex()
  return f"{hexstr[0:8]}-{hexstr[8:12]}-{hexstr[12:16]}-{hexstr[16:20]}-{hexstr[20:]}"
