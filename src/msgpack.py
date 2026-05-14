import struct
from typing import Any, Literal


def pack_int(n: int) -> bytes:
  if 0 <= n <= 127:
    return bytes([n])
  if -32 <= n < 0:
    return struct.pack("b", n)
  if -32768 <= n <= 32767:
    return b"\xd1" + struct.pack(">h", n)
  if -2147483648 <= n <= 2147483647:
    return b"\xd2" + struct.pack(">i", n)
  return b"\xd3" + struct.pack(">q", n)


def pack_float32(x: float) -> bytes:
  return b"\xca" + struct.pack(">f", x)


def pack_float64(x: float) -> bytes:
  return b"\xcb" + struct.pack(">d", x)


def pack_str(s: str) -> bytes:
  b = s.encode()
  l = len(b)
  if l < 32:
    return bytes([0xA0 | l]) + b

  if l < 256:
    return b"\xd9" + struct.pack("B", l) + b

  return b"\xda" + struct.pack(">H", l) + b


def pack_bin(b: bytes) -> bytes:
  l = len(b)
  if l < 256:
    return b"\xc4" + struct.pack("B", l) + b
  return b"\xc5" + struct.pack(">H", l) + b


def pack_array(arr: list) -> bytes:
  out: list[bytes] = []
  l = len(arr)
  if l < 16:
    out.append(bytes([0x90 | l]))
  else:
    out.append(b"\xdc" + struct.pack(">H", l))

  for item in arr:
    out.append(pack(item))

  return b"".join(out)


def pack_map(m: dict) -> bytes:
  out = []
  l = len(m)
  if l < 16:
    out.append(bytes([0x80 | l]))
  else:
    out.append(b"\xde" + struct.pack(">H", l))

  for k, v in m.items():
    out.append(pack(k))
    out.append(pack(v))

  return b"".join(out)


def pack(x: Any, float_precision: Literal["32", "64"] = "64") -> bytes:
  float_packer = pack_float32 if float_precision == "32" else pack_float64

  if isinstance(x, int):
    return pack_int(x)
  if isinstance(x, float):
    return float_packer(x)
  if isinstance(x, str):
    return pack_str(x)
  if isinstance(x, bytes):
    return pack_bin(x)
  if isinstance(x, list):
    return pack_array(x)
  if isinstance(x, dict):
    return pack_map(x)
  raise TypeError(f"Unsupported type: {type(x).__name__}")
