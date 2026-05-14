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
    out.append(encode_msgpack(item))

  return b"".join(out)


def pack_map(m: dict) -> bytes:
  out = []
  l = len(m)
  if l < 16:
    out.append(bytes([0x80 | l]))
  else:
    out.append(b"\xde" + struct.pack(">H", l))

  for k, v in m.items():
    out.append(encode_msgpack(k))
    out.append(encode_msgpack(v))

  return b"".join(out)


def encode_msgpack(x: Any, float_precision: Literal["32", "64"] = "64") -> bytes:
  float_packer = pack_float32 if float_precision == "32" else pack_float64

  if x is None:
    return b"\xc0"
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


def unpack_int8(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from("b", data, offset)[0], offset + 1


def unpack_uint8(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from("B", data, offset)[0], offset + 1


def unpack_int16(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from(">h", data, offset)[0], offset + 1


def unpack_uint16(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from(">H", data, offset)[0], offset + 2


def unpack_int32(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from(">i", data, offset)[0], offset + 1


def unpack_uint32(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from(">I", data, offset)[0], offset + 4


def unpack_int64(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from(">q", data, offset)[0], offset + 1


def unpack_uint64(data: bytes, offset: int) -> tuple[int, int]:
  return struct.unpack_from(">Q", data, offset)[0], offset + 8


def unpack_float32(data: bytes, offset: int) -> tuple[float, int]:
  return struct.unpack_from(">f", data, offset)[0], offset + 1


def unpack_float64(data: bytes, offset: int) -> tuple[float, int]:
  return struct.unpack_from(">d", data, offset)[0], offset + 1


def unpack_str(data: bytes, offset: int, length: int) -> tuple[str, int]:
  return data[offset : offset + length].decode(), offset + length


def unpack_bin(data: bytes, offset: int, length: int) -> tuple[bytes, int]:
  return data[offset : offset + length], offset + length


def unpack_array(data: bytes, offset: int, length: int) -> tuple[list, int]:
  arr = []
  for _ in range(length):
    item, offset = unpack(data, offset)
    arr.append(item)
  return arr, offset


def unpack_map(data: bytes, offset: int, length: int) -> tuple[dict, int]:
  m = {}
  for _ in range(length):
    key, offset = unpack(data, offset)
    val, offset = unpack(data, offset)
    m[key] = val
  return m, offset


def unpack(data: bytes, offset: int = 0) -> tuple[Any, int]:
  b = data[offset]
  offset += 1

  if b <= 0x7F:  # positive fixint
    return b, offset
  if b <= 0x8F:  # fixmap
    return unpack_map(data, offset, b & 0x0F)
  if b <= 0x9F:  # fixarray
    return unpack_array(data, offset, b & 0x0F)
  if b <= 0xBF:  # fixstring
    return unpack_str(data, offset, b & 0x1F)
  if b >= 0xE0:  # negative fixint
    return b - 256, offset

  match b:
    case 0xC0:
      return None, offset
    case 0xC2:
      return False, offset
    case 0xC3:
      return True, offset
    # bin
    case 0xC4:
      (n,) = struct.unpack_from("B", data, offset)
      return unpack_bin(data, offset + 1, n)
    case 0xC5:
      (n,) = struct.unpack_from(">H", data, offset)
      return unpack_bin(data, offset + 2, n)
    case 0xC6:
      (n,) = struct.unpack_from(">I", data, offset)
      return unpack_bin(data, offset + 4, n)
    # float
    case 0xCA:
      return unpack_float32(data, offset)
    case 0xCB:
      return unpack_float64(data, offset)
    # uint
    case 0xCD:
      return unpack_uint16(data, offset)
    case 0xCE:
      return unpack_uint32(data, offset)
    case 0xCF:
      return unpack_uint64(data, offset)
    # int
    case 0xCC:
      return unpack_uint8(data, offset)
    case 0xD0:
      return unpack_int8(data, offset)
    case 0xD1:
      return unpack_int16(data, offset)
    case 0xD2:
      return unpack_int32(data, offset)
    case 0xD3:
      return unpack_int64(data, offset)
    # str
    case 0xD9:
      (n,) = struct.unpack_from("B", data, offset)
      return unpack_str(data, offset + 1, n)
    case 0xDA:
      (n,) = struct.unpack_from(">H", data, offset)
      return unpack_str(data, offset + 2, n)
    case 0xDB:
      (n,) = struct.unpack_from(">I", data, offset)
      return unpack_str(data, offset + 4, n)
    # array
    case 0xDC:
      (n,) = struct.unpack_from(">H", data, offset)
      return unpack_array(data, offset + 2, n)
    case 0xDD:
      (n,) = struct.unpack_from(">I", data, offset)
      return unpack_array(data, offset + 4, n)
    # map
    case 0xDE:
      (n,) = struct.unpack_from(">H", data, offset)
      return unpack_map(data, offset + 2, n)
    case 0xDF:
      (n,) = struct.unpack_from(">I", data, offset)
      return unpack_map(data, offset + 4, n)

  raise ValueError(f"Unsupported msgpack byte: 0x{b:02x}")


def decode_msgpack(data: bytes) -> Any:
  value, _ = unpack(data)
  return value
