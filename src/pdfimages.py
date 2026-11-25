#!/usr/bin/env python3
"""
pdfimages.py - a dependency-free PDF image extractor (Python 3.10+, tested on 3.12/3.14).

Only the standard library is used.  It handles:

  * Damaged / non-standard files: junk before %PDF, bad or missing xref tables,
    wrong /Length values, truncated Flate data.  When the cross-reference data
    cannot be trusted the whole file is scanned and the xref is rebuilt.
  * Classic xref tables, xref streams, hybrid files, incremental updates,
    compressed object streams.
  * Standard-handler encryption with an empty (or supplied) password:
    RC4 40/128, AES-128 (V4) and AES-256 (V5, R5 and R6).
  * Filters: Flate, LZW, ASCIIHex, ASCII85, RunLength, Crypt, PNG/TIFF predictors.
  * XObject images AND inline images (BI/ID/EI), including those inside form
    XObjects, patterns, Type3 glyphs and annotation appearances.
  * Output formats
        DCTDecode      -> .jpg   (original bytes, untouched)
        JPXDecode      -> .jp2 / .j2k (original bytes)
        CCITTFaxDecode -> .tiff  (original G3/G4 data wrapped in a TIFF container)
        JBIG2Decode    -> .jb2   (standalone JBIG2 file incl. globals)
        everything else (Flate, LZW, raw ...) -> .png, with colour spaces
        Gray / RGB / CMYK / Indexed / ICCBased / Cal* / Lab / Separation / DeviceN
        converted, /Decode arrays honoured, /SMask, /Mask (stencil and colour
        key) merged as an alpha channel, 1/2/4/8/16 bits per component.

Command line:
    python pdfimages.py input.pdf [-o OUTDIR] [-p PASSWORD] [--min-size N]
                        [--no-inline] [--dedupe] [--manifest] [-q]

Library:
    from pdfimages import extract_images
    for img in extract_images("file.pdf"):
        open(f"x{img.obj}.{img.ext}", "wb").write(img.data)
"""

import argparse
import hashlib
import itertools
import json
import math
import os
import re
import struct
import sys
import zlib
from bisect import bisect_right
from collections import namedtuple
from dataclasses import dataclass, field

# ======================================================================
# PDF objects and the lexer
# ======================================================================


class PdfError(Exception):
  pass


class Name(str):
  __slots__ = ()

  def __repr__(self):
    return "/" + str.__str__(self)


class Keyword(str):
  __slots__ = ()


Ref = namedtuple("Ref", "num gen")


class Stream:
  """A stream object.  `data()` returns the still-encoded (but decrypted) bytes."""

  def __init__(self, dict_, raw, doc=None, num=0, gen=0):
    self.dict = dict_
    self.raw = raw
    self.doc = doc
    self.num = num
    self.gen = gen
    self.need_decrypt = False

  def data(self):
    if self.need_decrypt:
      self.raw = self.doc.crypt.decrypt_stream(self.raw, self.num, self.gen, self.dict)
      self.need_decrypt = False
    return self.raw

  def get(self, key, default=None):
    v = self.dict.get(key, default)
    return self.doc.resolve(v) if self.doc else v


_WS = frozenset(b"\x00\t\n\x0c\r ")
_DELIM = frozenset(b"()<>[]{}/%")
_REGULAR_END = _WS | _DELIM
_REF_RE = re.compile(
  rb"(\d+)[\x00\t\n\x0c\r ]+(\d+)[\x00\t\n\x0c\r ]+R(?=[\x00\t\n\x0c\r ()<>\[\]{}/%]|$)"
)
_INT_RE = re.compile(rb"[+-]?\d+")
_REAL_RE = re.compile(rb"[+-]?(?:\d+\.\d*|\.\d+)")
_LOOSE_NUM_RE = re.compile(rb"[+\-.\d]+")
_ESC = {110: 10, 114: 13, 116: 9, 98: 8, 102: 12}


class Lexer:
  def __init__(self, data, pos=0, refs=True):
    self.data = data
    self.pos = pos
    self.refs = refs

  def skip_ws(self):
    d = self.data
    n = len(d)
    p = self.pos
    while p < n:
      c = d[p]
      if c in _WS:
        p += 1
      elif c == 0x25:  # % comment
        while p < n and d[p] not in (10, 13):
          p += 1
      else:
        break
    self.pos = p

  def parse(self):
    self.skip_ws()
    d = self.data
    p = self.pos
    if p >= len(d):
      raise EOFError
    c = d[p]
    if c == 0x2F:
      return self._name()
    if c == 0x28:
      return self._string()
    if c == 0x3C:
      if d.startswith(b"<<", p):
        self.pos = p + 2
        return self._dict()
      return self._hex()
    if c == 0x5B:
      self.pos = p + 1
      return self._array()
    if c == 0x3E:
      if d.startswith(b">>", p):
        self.pos = p + 2
        return Keyword(">>")
      self.pos = p + 1
      return Keyword(">")
    if c in b"]{})":
      self.pos = p + 1
      return Keyword(chr(c))
    if self.refs and 0x30 <= c <= 0x39:
      m = _REF_RE.match(d, p)
      if m:
        self.pos = m.end()
        return Ref(int(m[1]), int(m[2]))
    e = p
    n = len(d)
    while e < n and d[e] not in _REGULAR_END:
      e += 1
    tok = d[p:e]
    self.pos = e
    if _INT_RE.fullmatch(tok):
      return int(tok)
    if _REAL_RE.fullmatch(tok):
      return float(tok)
    if tok == b"true":
      return True
    if tok == b"false":
      return False
    if tok == b"null":
      return None
    if _LOOSE_NUM_RE.fullmatch(tok):  # things like "--5", "1.2.3", "+-3"
      m = re.match(rb"([+-]*)(\d*\.?\d*)", tok)
      body = m[2]
      if body not in (b"", b"."):
        v = float(body) if b"." in body else int(body)
        return -v if b"-" in m[1] else v
      return 0
    return Keyword(tok.decode("latin-1"))

  def _name(self):
    d = self.data
    p = self.pos + 1
    e = p
    n = len(d)
    while e < n and d[e] not in _REGULAR_END:
      e += 1
    raw = d[p:e]
    self.pos = e
    if b"#" in raw:
      raw = re.sub(rb"#([0-9A-Fa-f]{2})", lambda m: bytes([int(m[1], 16)]), raw)
    return Name(raw.decode("latin-1"))

  def _string(self):
    d = self.data
    p = self.pos + 1
    n = len(d)
    depth = 1
    out = bytearray()
    while p < n:
      c = d[p]
      if c == 0x5C:
        p += 1
        if p >= n:
          break
        c = d[p]
        if c in _ESC:
          out.append(_ESC[c])
          p += 1
        elif 0x30 <= c <= 0x37:
          v = 0
          k = 0
          while k < 3 and p < n and 0x30 <= d[p] <= 0x37:
            v = v * 8 + d[p] - 48
            p += 1
            k += 1
          out.append(v & 255)
        elif c == 13:
          p += 1
          if p < n and d[p] == 10:
            p += 1
        elif c == 10:
          p += 1
        else:
          out.append(c)
          p += 1
      elif c == 0x28:
        depth += 1
        out.append(c)
        p += 1
      elif c == 0x29:
        depth -= 1
        p += 1
        if depth == 0:
          break
        out.append(c)
      else:
        out.append(c)
        p += 1
    self.pos = p
    return bytes(out)

  def _hex(self):
    d = self.data
    p = self.pos + 1
    e = d.find(b">", p)
    if e < 0:
      e = len(d)
    raw = re.sub(rb"[^0-9A-Fa-f]", b"", d[p:e])
    self.pos = min(e + 1, len(d))
    if len(raw) & 1:
      raw += b"0"
    return bytes.fromhex(raw.decode("ascii"))

  def _array(self):
    out = []
    while True:
      try:
        o = self.parse()
      except EOFError:
        break
      if isinstance(o, Keyword):
        if o == "]":
          break
        if o in ("endobj", "stream", "endstream"):
          self.pos -= len(o)
          break
        continue
      out.append(o)
    return out

  def _dict(self):
    out = {}
    while True:
      try:
        k = self.parse()
      except EOFError:
        break
      if isinstance(k, Keyword):
        if k == ">>":
          break
        if k in ("endobj", "stream", "endstream"):
          self.pos -= len(k)
          break
        continue
      if not isinstance(k, Name):
        continue
      try:
        v = self.parse()
      except EOFError:
        out[k] = None
        break
      if isinstance(v, Keyword):
        if v == ">>":
          out[k] = None
          break
        if v in ("endobj", "stream", "endstream"):
          self.pos -= len(v)
          break
        v = None
      out[k] = v
    return out


# ======================================================================
# Stream filters
# ======================================================================

_FILTER_ALIAS = {
  "AHx": "ASCIIHexDecode",
  "A85": "ASCII85Decode",
  "LZW": "LZWDecode",
  "Fl": "FlateDecode",
  "RL": "RunLengthDecode",
  "CCF": "CCITTFaxDecode",
  "DCT": "DCTDecode",
}
_IMAGE_FILTERS = {"DCTDecode", "JPXDecode", "JBIG2Decode", "CCITTFaxDecode"}


def _ascii_hex(data):
  end = data.find(b">")
  if end >= 0:
    data = data[:end]
  data = re.sub(rb"[^0-9A-Fa-f]", b"", data)
  if len(data) & 1:
    data += b"0"
  return bytes.fromhex(data.decode("ascii"))


def _ascii85(data):
  data = data.strip()
  if data.startswith(b"<~"):
    data = data[2:]
  end = data.find(b"~")
  if end >= 0:
    data = data[:end]
  out = bytearray()
  grp = []
  for c in data:
    if c in _WS:
      continue
    if c == 0x7A and not grp:
      out += b"\0\0\0\0"
      continue
    if not 0x21 <= c <= 0x75:
      continue
    grp.append(c - 33)
    if len(grp) == 5:
      v = 0
      for g in grp:
        v = v * 85 + g
      out += (v & 0xFFFFFFFF).to_bytes(4, "big")
      grp = []
  if len(grp) > 1:
    k = len(grp)
    grp += [84] * (5 - k)
    v = 0
    for g in grp:
      v = v * 85 + g
    out += (v & 0xFFFFFFFF).to_bytes(4, "big")[: k - 1]
  return bytes(out)


def _run_length(data):
  out = bytearray()
  i = 0
  n = len(data)
  while i < n:
    ln = data[i]
    i += 1
    if ln == 128:
      break
    if ln < 128:
      out += data[i : i + ln + 1]
      i += ln + 1
    else:
      if i >= n:
        break
      out += data[i : i + 1] * (257 - ln)
      i += 1
  return bytes(out)


def _inflate_partial(data, wbits):
  d = zlib.decompressobj(wbits)
  out = bytearray()
  step = 4096
  for i in range(0, len(data), step):
    chunk = data[i : i + step]
    saved = d.copy()
    try:
      out += d.decompress(chunk)
    except zlib.error:
      for b in chunk:  # salvage everything up to the exact corrupt byte
        try:
          out += saved.decompress(bytes([b]))
        except zlib.error:
          return bytes(out)
      return bytes(out)
    if d.eof:
      break
  return bytes(out)


def _flate(data):
  try:
    return zlib.decompress(data)
  except zlib.error:
    pass
  stripped = data.lstrip(b"\r\n \t\x00")
  for blob, wbits in ((data, 15), (stripped, 15), (data, -15), (data[2:], -15)):
    out = _inflate_partial(blob, wbits)
    if out:
      return out
  return b""


def _lzw(data, early=1):
  out = bytearray()
  table = [bytes([i]) for i in range(256)] + [b"", b""]
  bits = 9
  buf = 0
  nbits = 0
  prev = None
  for byte in data:
    buf = (buf << 8) | byte
    nbits += 8
    while nbits >= bits:
      code = (buf >> (nbits - bits)) & ((1 << bits) - 1)
      nbits -= bits
      buf &= (1 << nbits) - 1
      if code == 256:
        del table[258:]
        bits = 9
        prev = None
        continue
      if code == 257:
        return bytes(out)
      if prev is None:
        if code >= len(table):
          return bytes(out)
        entry = table[code]
        out += entry
        prev = entry
        continue
      if code < len(table):
        entry = table[code]
      elif code == len(table):
        entry = prev + prev[:1]
      else:
        return bytes(out)
      out += entry
      if len(table) < 4096:
        table.append(prev + entry[:1])
      prev = entry
      n = len(table) + early
      bits = 9 if n < 512 else 10 if n < 1024 else 11 if n < 2048 else 12
  return bytes(out)


def _add8(a, b):
  return (a + b) & 255


def _predict(data, p):
  pred = int(p.get("Predictor", 1) or 1)
  if pred <= 1:
    return data
  colors = int(p.get("Colors", 1) or 1)
  bpc = int(p.get("BitsPerComponent", 8) or 8)
  cols = int(p.get("Columns", 1) or 1)
  rowlen = (cols * colors * bpc + 7) // 8
  if rowlen <= 0:
    return data
  if pred == 2:  # TIFF predictor
    out = bytearray(data)
    if bpc == 8:
      for r in range(0, len(out), rowlen):
        for c in range(colors):
          out[r + c : r + rowlen : colors] = bytes(
            itertools.accumulate(out[r + c : r + rowlen : colors], _add8)
          )
    elif bpc == 16:
      for r in range(0, len(out) - rowlen + 1, rowlen):
        vals = list(struct.unpack(f">{rowlen // 2}H", out[r : r + rowlen // 2 * 2]))
        for c in range(colors):
          vals[c::colors] = itertools.accumulate(
            vals[c::colors], lambda a, b: (a + b) & 0xFFFF
          )
        out[r : r + rowlen // 2 * 2] = struct.pack(f">{len(vals)}H", *vals)
    elif bpc in (1, 2, 4):
      per = 8 // bpc
      mask = (1 << bpc) - 1
      for r in range(0, len(out) - rowlen + 1, rowlen):
        vals = []
        for byte in out[r : r + rowlen]:
          vals.extend((byte >> (8 - bpc * (i + 1))) & mask for i in range(per))
        vals = vals[: cols * colors]
        for c in range(colors):
          vals[c::colors] = itertools.accumulate(
            vals[c::colors], lambda a, b: (a + b) & mask
          )
        vals += [0] * (rowlen * per - len(vals))
        row = bytearray()
        for i in range(0, len(vals), per):
          v = 0
          for x in vals[i : i + per]:
            v = (v << bpc) | x
          row.append(v)
        out[r : r + rowlen] = row
    return bytes(out)
  # PNG predictors (10-15): every row has its own filter-type byte
  bpp = max(1, (colors * bpc + 7) // 8)
  stride = rowlen + 1
  nrows = (len(data) + stride - 1) // stride
  out = bytearray(nrows * rowlen)
  prev = bytearray(rowlen)
  for r in range(nrows):
    chunk = data[r * stride : (r + 1) * stride]
    ft = chunk[0]
    row = bytearray(chunk[1:])
    if len(row) < rowlen:
      row += bytes(rowlen - len(row))
    if ft == 1:
      if bpp == 1:
        row = bytearray(itertools.accumulate(row, _add8))
      else:
        for c in range(bpp):
          row[c::bpp] = bytes(itertools.accumulate(row[c::bpp], _add8))
    elif ft == 2:
      row = bytearray([(a + b) & 255 for a, b in zip(row, prev)])
    elif ft == 3:
      for i in range(rowlen):
        a = row[i - bpp] if i >= bpp else 0
        row[i] = (row[i] + ((a + prev[i]) >> 1)) & 255
    elif ft == 4:
      for i in range(rowlen):
        if i >= bpp:
          a = row[i - bpp]
          c = prev[i - bpp]
        else:
          a = c = 0
        b = prev[i]
        pa = abs(b - c)
        pb = abs(a - c)
        pc = abs(a + b - 2 * c)
        pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
        row[i] = (row[i] + pr) & 255
    out[r * rowlen : (r + 1) * rowlen] = row
    prev = row
  return bytes(out)


def get_filters(doc, d):
  """Returns two parallel lists: canonical filter names, decode-parameter dicts."""
  r = doc.resolve
  f = r(d.get("Filter"))
  p = r(d.get("DecodeParms", d.get("DP")))
  if f is None:
    return [], []
  if not isinstance(f, list):
    f = [f]
    p = [p[0] if isinstance(p, list) and p else p]
  elif not isinstance(p, list):
    p = [p] + [None] * (len(f) - 1) if isinstance(p, dict) else [None] * len(f)
  p = list(p) + [None] * (len(f) - len(p))
  names = []
  parms = []
  for fi, pi in zip(f, p):
    fi = r(fi)
    pi = r(pi)
    names.append(_FILTER_ALIAS.get(str(fi), str(fi)))
    parms.append({k: r(v) for k, v in pi.items()} if isinstance(pi, dict) else {})
  return names, parms


def decode_stream(doc, stream):
  """Apply all non-image filters.  Returns (data, image_filter_name_or_None, its_params)."""
  data = stream.data()
  names, parms = get_filters(doc, stream.dict)
  for name, p in zip(names, parms):
    if name in _IMAGE_FILTERS:
      return data, name, p
    if name == "FlateDecode":
      data = _predict(_flate(data), p)
    elif name == "LZWDecode":
      data = _predict(_lzw(data, int(p.get("EarlyChange", 1))), p)
    elif name == "ASCIIHexDecode":
      data = _ascii_hex(data)
    elif name == "ASCII85Decode":
      data = _ascii85(data)
    elif name == "RunLengthDecode":
      data = _run_length(data)
    elif name == "Crypt":
      pass
    else:
      raise PdfError("unsupported filter " + name)
  return data, None, {}


# ======================================================================
# Cryptography: RC4 + AES (pure Python) and the standard security handler
# ======================================================================


def rc4(key, data):
  s = list(range(256))
  j = 0
  kl = len(key)
  for i in range(256):
    j = (j + s[i] + key[i % kl]) & 255
    s[i], s[j] = s[j], s[i]
  out = bytearray(len(data))
  i = j = 0
  for n, c in enumerate(data):
    i = (i + 1) & 255
    a = s[i]
    j = (j + a) & 255
    b = s[j]
    s[i] = b
    s[j] = a
    out[n] = c ^ s[(a + b) & 255]
  return bytes(out)


def _build_aes_tables():
  sbox = [0] * 256
  p = q = 1
  while True:
    p = (p ^ ((p << 1) & 0xFF) ^ (0x1B if p & 0x80 else 0)) & 0xFF
    q ^= (q << 1) & 0xFF
    q ^= (q << 2) & 0xFF
    q ^= (q << 4) & 0xFF
    if q & 0x80:
      q ^= 0x09
    x = q
    for k in range(1, 5):
      x ^= ((q << k) | (q >> (8 - k))) & 0xFF
    sbox[p] = x ^ 0x63
    if p == 1:
      break
  sbox[0] = 0x63
  inv = [0] * 256
  for i, v in enumerate(sbox):
    inv[v] = i

  def mul(a, b):
    res = 0
    while b:
      if b & 1:
        res ^= a
      a = ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else a << 1
      b >>= 1
    return res

  def ror(v, n):
    return ((v >> n) | (v << (32 - n))) & 0xFFFFFFFF

  te = [[], [], [], []]
  td = [[], [], [], []]
  for x in range(256):
    s = sbox[x]
    t = (mul(s, 2) << 24) | (s << 16) | (s << 8) | mul(s, 3)
    i = inv[x]
    u = (mul(i, 14) << 24) | (mul(i, 9) << 16) | (mul(i, 13) << 8) | mul(i, 11)
    for k in range(4):
      te[k].append(ror(t, 8 * k))
      td[k].append(ror(u, 8 * k))
  return sbox, inv, te, td


_SBOX, _ISBOX, _TE, _TD = _build_aes_tables()


class AES:
  """AES-128/192/256 in CBC mode (no padding handling)."""

  def __init__(self, key):
    if len(key) not in (16, 24, 32):
      raise PdfError("bad AES key length")
    S = _SBOX
    nk = len(key) // 4
    self.nr = nr = nk + 6
    w = list(struct.unpack(f">{nk}I", key))

    def sub(t):
      return (
        (S[t >> 24] << 24)
        | (S[(t >> 16) & 255] << 16)
        | (S[(t >> 8) & 255] << 8)
        | S[t & 255]
      )

    rcon = 1
    for i in range(nk, 4 * (nr + 1)):
      t = w[i - 1]
      if i % nk == 0:
        t = sub(((t << 8) | (t >> 24)) & 0xFFFFFFFF) ^ (rcon << 24)
        rcon = ((rcon << 1) ^ 0x11B) & 0xFF if rcon & 0x80 else rcon << 1
      elif nk > 6 and i % nk == 4:
        t = sub(t)
      w.append(w[i - nk] ^ t)
    self.ek = w
    t0, t1, t2, t3 = _TD
    dk = []
    for r in range(nr, -1, -1):
      rk = w[4 * r : 4 * r + 4]
      if 0 < r < nr:
        rk = [
          t0[S[x >> 24]]
          ^ t1[S[(x >> 16) & 255]]
          ^ t2[S[(x >> 8) & 255]]
          ^ t3[S[x & 255]]
          for x in rk
        ]
      dk += rk
    self.dk = dk

  def decrypt_cbc(self, data, iv):
    T0, T1, T2, T3 = _TD
    IS = _ISBOX
    dk = self.dk
    nr = self.nr
    out = []
    p0, p1, p2, p3 = struct.unpack(">4I", iv)
    for c0, c1, c2, c3 in struct.iter_unpack(">4I", data[: len(data) // 16 * 16]):
      s0 = c0 ^ dk[0]
      s1 = c1 ^ dk[1]
      s2 = c2 ^ dk[2]
      s3 = c3 ^ dk[3]
      k = 4
      for _ in range(nr - 1):
        t0 = (
          T0[s0 >> 24]
          ^ T1[(s3 >> 16) & 255]
          ^ T2[(s2 >> 8) & 255]
          ^ T3[s1 & 255]
          ^ dk[k]
        )
        t1 = (
          T0[s1 >> 24]
          ^ T1[(s0 >> 16) & 255]
          ^ T2[(s3 >> 8) & 255]
          ^ T3[s2 & 255]
          ^ dk[k + 1]
        )
        t2 = (
          T0[s2 >> 24]
          ^ T1[(s1 >> 16) & 255]
          ^ T2[(s0 >> 8) & 255]
          ^ T3[s3 & 255]
          ^ dk[k + 2]
        )
        t3 = (
          T0[s3 >> 24]
          ^ T1[(s2 >> 16) & 255]
          ^ T2[(s1 >> 8) & 255]
          ^ T3[s0 & 255]
          ^ dk[k + 3]
        )
        s0, s1, s2, s3 = t0, t1, t2, t3
        k += 4
      o0 = (
        (IS[s0 >> 24] << 24)
        | (IS[(s3 >> 16) & 255] << 16)
        | (IS[(s2 >> 8) & 255] << 8)
        | IS[s1 & 255]
      ) ^ dk[k]
      o1 = (
        (IS[s1 >> 24] << 24)
        | (IS[(s0 >> 16) & 255] << 16)
        | (IS[(s3 >> 8) & 255] << 8)
        | IS[s2 & 255]
      ) ^ dk[k + 1]
      o2 = (
        (IS[s2 >> 24] << 24)
        | (IS[(s1 >> 16) & 255] << 16)
        | (IS[(s0 >> 8) & 255] << 8)
        | IS[s3 & 255]
      ) ^ dk[k + 2]
      o3 = (
        (IS[s3 >> 24] << 24)
        | (IS[(s2 >> 16) & 255] << 16)
        | (IS[(s1 >> 8) & 255] << 8)
        | IS[s0 & 255]
      ) ^ dk[k + 3]
      out.append(struct.pack(">4I", o0 ^ p0, o1 ^ p1, o2 ^ p2, o3 ^ p3))
      p0, p1, p2, p3 = c0, c1, c2, c3
    return b"".join(out)

  def encrypt_cbc(self, data, iv):
    T0, T1, T2, T3 = _TE
    S = _SBOX
    ek = self.ek
    nr = self.nr
    out = []
    p0, p1, p2, p3 = struct.unpack(">4I", iv)
    for c0, c1, c2, c3 in struct.iter_unpack(">4I", data[: len(data) // 16 * 16]):
      s0 = c0 ^ p0 ^ ek[0]
      s1 = c1 ^ p1 ^ ek[1]
      s2 = c2 ^ p2 ^ ek[2]
      s3 = c3 ^ p3 ^ ek[3]
      k = 4
      for _ in range(nr - 1):
        t0 = (
          T0[s0 >> 24]
          ^ T1[(s1 >> 16) & 255]
          ^ T2[(s2 >> 8) & 255]
          ^ T3[s3 & 255]
          ^ ek[k]
        )
        t1 = (
          T0[s1 >> 24]
          ^ T1[(s2 >> 16) & 255]
          ^ T2[(s3 >> 8) & 255]
          ^ T3[s0 & 255]
          ^ ek[k + 1]
        )
        t2 = (
          T0[s2 >> 24]
          ^ T1[(s3 >> 16) & 255]
          ^ T2[(s0 >> 8) & 255]
          ^ T3[s1 & 255]
          ^ ek[k + 2]
        )
        t3 = (
          T0[s3 >> 24]
          ^ T1[(s0 >> 16) & 255]
          ^ T2[(s1 >> 8) & 255]
          ^ T3[s2 & 255]
          ^ ek[k + 3]
        )
        s0, s1, s2, s3 = t0, t1, t2, t3
        k += 4
      p0 = (
        (S[s0 >> 24] << 24)
        | (S[(s1 >> 16) & 255] << 16)
        | (S[(s2 >> 8) & 255] << 8)
        | S[s3 & 255]
      ) ^ ek[k]
      p1 = (
        (S[s1 >> 24] << 24)
        | (S[(s2 >> 16) & 255] << 16)
        | (S[(s3 >> 8) & 255] << 8)
        | S[s0 & 255]
      ) ^ ek[k + 1]
      p2 = (
        (S[s2 >> 24] << 24)
        | (S[(s3 >> 16) & 255] << 16)
        | (S[(s0 >> 8) & 255] << 8)
        | S[s1 & 255]
      ) ^ ek[k + 2]
      p3 = (
        (S[s3 >> 24] << 24)
        | (S[(s0 >> 16) & 255] << 16)
        | (S[(s1 >> 8) & 255] << 8)
        | S[s2 & 255]
      ) ^ ek[k + 3]
      out.append(struct.pack(">4I", p0, p1, p2, p3))
    return b"".join(out)


def _md5(data):
  try:
    return hashlib.md5(data, usedforsecurity=False)
  except TypeError:  # very old builds
    return hashlib.md5(data)


_PAD = bytes.fromhex("28BF4E5E4E758A4164004E56FFFA01082E2E00B6D0683E802F0CA9FE6453697A")


def _hash_r6(password, salt, udata=b""):
  """ISO 32000-2 algorithm 2.B."""
  k = hashlib.sha256(password + salt + udata).digest()
  i = 0
  e = b"\x00"
  while i < 64 or e[-1] > i - 32:
    k1 = (password + k + udata) * 64
    e = AES(k[:16]).encrypt_cbc(k1, k[16:32])
    mod = sum(e[:16]) % 3
    k = (hashlib.sha256, hashlib.sha384, hashlib.sha512)[mod](e).digest()
    i += 1
  return k[:32]


class Crypt:
  """Standard security handler (empty user password by default)."""

  def __init__(self, doc, enc, id0, password):
    r = doc.resolve
    self.doc = doc
    if r(enc.get("Filter")) != "Standard":
      raise PdfError("unsupported security handler {!r}".format(r(enc.get("Filter"))))
    self.V = int(r(enc.get("V", 0)) or 0)
    self.R = int(r(enc.get("R", 2)) or 2)
    O = r(enc.get("O")) or b""
    U = r(enc.get("U")) or b""
    P = int(r(enc.get("P", 0)) or 0)
    length = int(r(enc.get("Length", 40)) or 40)
    enc_meta = r(enc.get("EncryptMetadata"))
    enc_meta = True if enc_meta is None else bool(enc_meta)
    self.cf = {}
    stm = strf = "RC4"
    if self.V >= 4:
      cf = r(enc.get("CF")) or {}
      for name, v in cf.items():
        v = r(v) or {}
        cfm = str(r(v.get("CFM")))
        self.cf[str(name)] = {"V2": "RC4", "AESV2": "AESV2", "AESV3": "AESV3"}.get(
          cfm, "Identity"
        )
      stm = self._cf(r(enc.get("StmF")))
      strf = self._cf(r(enc.get("StrF")))
      if self.V == 4:
        length = int(r(enc.get("Length", 128)) or 128)
        if length < 40:
          length *= 8
    self.stm_method, self.str_method = stm, strf
    pw = password if isinstance(password, bytes) else str(password).encode("utf-8")
    self.valid = True
    if self.V >= 5:
      pw = pw[:127]
      ok = False
      h = (
        (lambda p, s, u=b"": hashlib.sha256(p + s + u).digest())
        if self.R == 5
        else _hash_r6
      )
      if h(pw, U[32:40]) == U[:32]:
        ik = h(pw, U[40:48])
        self.key = AES(ik).decrypt_cbc(r(enc.get("UE")), bytes(16))[:32]
        ok = True
      elif h(pw, O[32:40], U[:48]) == O[:32]:
        ik = h(pw, O[40:48], U[:48])
        self.key = AES(ik).decrypt_cbc(r(enc.get("OE")), bytes(16))[:32]
        ok = True
      if not ok:
        self.valid = False
        ik = h(pw, U[40:48])
        self.key = AES(ik).decrypt_cbc(r(enc.get("UE")) or bytes(32), bytes(16))[:32]
    else:
      n = 5 if self.R == 2 else max(5, min(16, length // 8))
      padded = (pw + _PAD)[:32]
      h = _md5(
        padded
        + O[:32]
        + struct.pack("<I", P & 0xFFFFFFFF)
        + id0
        + (b"\xff\xff\xff\xff" if self.R >= 4 and not enc_meta else b"")
      )
      d = h.digest()
      if self.R >= 3:
        for _ in range(50):
          d = _md5(d[:n]).digest()
      self.key = d[:n]
      if self.R == 2:
        chk = rc4(self.key, _PAD)
        self.valid = chk == U[:32]
      else:
        x = rc4(self.key, _md5(_PAD + id0).digest())
        for i in range(1, 20):
          x = rc4(bytes(b ^ i for b in self.key), x)
        self.valid = x[:16] == U[:16]

  def _cf(self, name):
    name = str(name or "Identity")
    if name == "Identity":
      return "Identity"
    return self.cf.get(name, "RC4")

  def _object_key(self, num, gen, aes):
    if self.V >= 5:
      return self.key
    k = (
      self.key
      + struct.pack("<I", num)[:3]
      + struct.pack("<I", gen)[:2]
      + (b"sAlT" if aes else b"")
    )
    return _md5(k).digest()[: min(len(self.key) + 5, 16)]

  def _decrypt(self, data, num, gen, method):
    if method == "Identity" or not data:
      return data
    key = self._object_key(num, gen, method.startswith("AES"))
    if method == "RC4":
      return rc4(key, data)
    if len(data) < 32:
      return b""
    plain = AES(key).decrypt_cbc(data[16:], data[:16])
    if plain:
      pad = plain[-1]
      if 1 <= pad <= 16:
        plain = plain[:-pad]
    return plain

  def decrypt_stream(self, raw, num, gen, d):
    method = self.stm_method
    names, parms = get_filters(self.doc, d)
    for n, p in zip(names, parms):
      if n == "Crypt":
        method = self._cf(p.get("Name", "Identity"))
    return self._decrypt(raw, num, gen, method)

  def decrypt_obj(self, o, num, gen):
    if isinstance(o, bytes):
      return self._decrypt(o, num, gen, self.str_method)
    if isinstance(o, list):
      return [self.decrypt_obj(x, num, gen) for x in o]
    if isinstance(o, dict):
      return {k: self.decrypt_obj(v, num, gen) for k, v in o.items()}
    return o


# ======================================================================
# The document: xref handling, repair, object loading
# ======================================================================

_OBJ_RE = re.compile(
  rb"(?<![0-9])(\d{1,10})[ \t\r\n\x00\x0c]+(\d{1,5})[ \t\r\n\x00\x0c]+obj(?![A-Za-z])"
)


class PdfDocument:
  def __init__(self, data, password="", warn=None):
    i = data.find(b"%PDF-", 0, 8192)
    self.data = data[i:] if i > 0 else data
    self.warn = warn or (lambda m: None)
    self.xref = {}
    self.trailer = {}
    self.cache = {}
    self._stream_cache = {}
    self._objstm = {}
    self._resolving = set()
    self.crypt = None
    self._enc_num = None
    self._rebuilt = False
    self._password = password
    good = False
    try:
      self._read_xref_chain(self._find_startxref())
      self._setup_encryption()
      root = self.resolve(self.trailer.get("Root"))
      good = isinstance(root, dict) and "Pages" in root
    except Exception as e:  # noqa: BLE001 - any damage means "rebuild"
      self.warn(f"xref unusable ({e}); rebuilding")
    if not good:
      self._rebuild()

  # ---- xref reading -------------------------------------------------
  def _find_startxref(self):
    i = self.data.rfind(b"startxref")
    if i < 0:
      raise PdfError("no startxref")
    v = Lexer(self.data, i + 9, refs=False).parse()
    if not isinstance(v, int):
      raise PdfError("bad startxref")
    return v

  def _read_xref_chain(self, pos):
    seen = set()
    queue = [pos]
    while queue:
      p = queue.pop(0)
      if p in seen or not 0 <= p < len(self.data):
        continue
      seen.add(p)
      t = self._read_xref_section(p)
      for k, v in t.items():
        self.trailer.setdefault(k, v)
      if isinstance(t.get("XRefStm"), int):
        queue.insert(0, t["XRefStm"])
      if isinstance(t.get("Prev"), (int, float)):
        queue.append(int(t["Prev"]))

  def _read_xref_section(self, pos):
    d = self.data
    lx = Lexer(d, pos, refs=False)
    lx.skip_ws()
    if not d.startswith(b"xref", lx.pos):
      return self._read_xref_stream(lx.pos)
    lx.pos += 4
    while True:
      tok = lx.parse()
      if isinstance(tok, Keyword) and tok == "trailer":
        break
      count = lx.parse()
      if not isinstance(tok, int) or not isinstance(count, int):
        raise PdfError("bad xref subsection")
      start = tok
      for i in range(count):
        save = lx.pos
        a = lx.parse()
        if isinstance(a, Keyword):
          lx.pos = save
          break
        b = lx.parse()
        kind = lx.parse()
        if not (isinstance(a, int) and isinstance(b, int)):
          raise PdfError("bad xref entry")
        if i == 0 and start == 1 and kind == "f" and b == 65535:
          start = 0  # common off-by-one in broken writers
        num = start + i
        if kind == "n" and a > 0:
          self.xref.setdefault(num, (1, a, b))
        else:
          self.xref.setdefault(num, (0, 0, 0))
    t = lx.parse()
    if not isinstance(t, dict):
      raise PdfError("bad trailer")
    return t

  def _read_xref_stream(self, pos):
    _num, _gen, st = self._parse_indirect(pos)
    if not isinstance(st, Stream) or self.resolve(st.dict.get("Type")) != "XRef":
      raise PdfError("not an xref stream")
    d = st.dict
    W = [int(x) for x in d["W"]]
    index = d.get("Index") or [0, int(d.get("Size", 0))]
    data, _, _ = decode_stream(self, st)
    rowlen = sum(W)
    offs = [0, W[0], W[0] + W[1], rowlen]
    i = 0
    for a in range(0, len(index) - 1, 2):
      start, count = index[a], index[a + 1]
      for k in range(count):
        row = data[i : i + rowlen]
        i += rowlen
        if len(row) < rowlen:
          break
        f = [int.from_bytes(row[offs[j] : offs[j + 1]], "big") for j in range(3)]
        t = f[0] if W[0] else 1
        if t == 1:
          self.xref.setdefault(start + k, (1, f[1], f[2]))
        elif t == 2:
          self.xref.setdefault(start + k, (2, f[1], f[2]))
        else:
          self.xref.setdefault(start + k, (0, 0, 0))
    return d

  # ---- repair ---------------------------------------------------------
  def _enclosing_object(self, starts, pos):
    i = bisect_right(starts, pos) - 1
    return starts[i] if i >= 0 else None

  def _rebuild(self):
    self._rebuilt = True
    self.xref = {}
    self.cache.clear()
    self._stream_cache.clear()
    self._objstm.clear()
    data = self.data
    offset_to_num = {}
    for m in _OBJ_RE.finditer(data):
      n = int(m[1])
      self.xref[n] = (1, m.start(), int(m[2]))
      offset_to_num[m.start()] = n
    starts = sorted(offset_to_num)
    trailer = {}
    for m in re.finditer(rb"trailer", data):
      try:
        t = Lexer(data, m.end(), refs=True).parse()
      except Exception as e:  # noqa: BLE001
        self.warn(f"bad trailer: {e}")
        continue
      if isinstance(t, dict):
        trailer.update(t)
    for m in re.finditer(rb"/Type\s*/XRef(?![A-Za-z])", data):
      s = self._enclosing_object(starts, m.start())
      if s is None:
        continue
      try:
        _, _, xobj = self._parse_indirect(s)
      except Exception as e:  # noqa: BLE001
        self.warn(f"bad xref stream: {e}")
        continue
      t = xobj.dict if isinstance(xobj, Stream) else xobj
      if isinstance(t, dict):
        for k in ("Root", "Info", "Encrypt", "ID"):
          if k in t:
            trailer[k] = t[k]
    self.trailer = trailer
    if self.crypt is None:
      try:
        self._setup_encryption()
      except Exception as e:  # noqa: BLE001
        self.warn(f"cannot set up encryption: {e}")
    # register objects that live inside object streams
    stm_offsets = {}
    for m in re.finditer(rb"/Type\s*/ObjStm(?![A-Za-z])", data):
      s = self._enclosing_object(starts, m.start())
      if s is not None:
        stm_offsets[offset_to_num[s]] = s
    for snum, soff in sorted(stm_offsets.items(), key=lambda kv: kv[1]):
      try:
        _, pairs = self._objstm_entries(snum)
      except Exception as e:  # noqa: BLE001
        self.warn(f"object stream {snum} unreadable: {e}")
        continue
      for idx, (onum, _) in enumerate(pairs):
        cur = self.xref.get(onum)
        if cur and cur[0] == 1 and cur[1] > soff:
          continue
        self.xref[onum] = (2, snum, idx)
    root = self.resolve(self.trailer.get("Root"))
    if not isinstance(root, dict):
      for num in sorted(self.xref):
        try:
          o = self.get(num)
        except Exception as e:  # noqa: BLE001
          self.warn(f"object {num}: {e}")
          continue
        if isinstance(o, dict) and o.get("Type") == "Catalog":
          self.trailer["Root"] = Ref(num, 0)
          break

  def _setup_encryption(self):
    enc = self.trailer.get("Encrypt")
    if enc is None:
      return
    if isinstance(enc, Ref):
      self._enc_num = enc.num
    self.crypt = None
    d = self.resolve(enc)
    if not isinstance(d, dict):
      return
    ids = self.resolve(self.trailer.get("ID"))
    id0 = self.resolve(ids[0]) if isinstance(ids, list) and ids else b""
    self.crypt = Crypt(self, d, id0 if isinstance(id0, bytes) else b"", self._password)
    if not self.crypt.valid:
      self.warn("password check failed - output may be garbage (use --password)")
    self.cache.clear()
    self._stream_cache.clear()
    self._objstm.clear()

  # ---- object loading ----------------------------------------------------
  def _parse_indirect(self, offset):
    data = self.data
    lx = Lexer(data, offset)
    num = lx.parse()
    gen = lx.parse()
    kw = lx.parse()
    if not (
      isinstance(num, int)
      and isinstance(gen, int)
      and isinstance(kw, Keyword)
      and kw == "obj"
    ):
      raise PdfError(f"no object at offset {offset}")
    try:
      obj = lx.parse()
    except EOFError:
      obj = None
    if isinstance(obj, Keyword):
      obj = None
    if isinstance(obj, dict):
      lx.skip_ws()
      if data.startswith(b"stream", lx.pos):
        p = lx.pos + 6
        if data.startswith(b"\r\n", p):
          p += 2
        elif data[p : p + 1] in (b"\n", b"\r"):
          p += 1
        length = obj.get("Length")
        if isinstance(length, Ref):
          length = self.resolve(length)
        end = None
        if isinstance(length, int) and length >= 0 and p + length <= len(data):
          tail = data[p + length : p + length + 24].lstrip(b"\r\n \t\x00")
          if tail.startswith((b"endstream", b"endobj")):
            end = p + length
        if end is None:
          e = data.find(b"endstream", p)
          if e < 0:
            e = data.find(b"endobj", p)
          if e < 0:
            e = len(data)
          if data[e - 2 : e] == b"\r\n":
            e -= 2
          elif data[e - 1 : e] in (b"\n", b"\r"):
            e -= 1
          end = max(e, p)
        obj = Stream(obj, data[p:end], self, num, gen)
    return num, gen, obj

  def _objstm_entries(self, snum):
    if snum in self._objstm:
      return self._objstm[snum]
    st = self.get(snum)
    if not isinstance(st, Stream):
      raise PdfError(f"object stream {snum} missing")
    data, _, _ = decode_stream(self, st)
    n = int(self.resolve(st.dict.get("N")))
    first = int(self.resolve(st.dict.get("First")))
    lx = Lexer(data, 0, refs=False)
    pairs = []
    for _ in range(n):
      try:
        a = lx.parse()
        b = lx.parse()
      except EOFError:
        break
      if not (isinstance(a, int) and isinstance(b, int)):
        break
      pairs.append((a, b))
    self._objstm[snum] = (data, first, pairs)
    return data, first, pairs

  def get(self, num):
    if num in self.cache:
      return self.cache[num]
    if num in self._stream_cache:
      return self._stream_cache[num]
    ent = self.xref.get(num)
    if not ent or ent[0] == 0 or num in self._resolving:
      return None
    self._resolving.add(num)
    try:
      obj = self._load(num, ent)
    except PdfError:
      obj = KeyError  # sentinel: needs repair
    finally:
      self._resolving.discard(num)
    if obj is KeyError:
      if self._rebuilt:
        return None
      self._rebuild()
      return self.get(num)
    if isinstance(obj, Stream):
      if len(self._stream_cache) > 24:
        self._stream_cache.pop(next(iter(self._stream_cache)))
      self._stream_cache[num] = obj
    else:
      self.cache[num] = obj
    return obj

  def _load(self, num, ent):
    if ent[0] == 1:
      try:
        n, g, obj = self._parse_indirect(ent[1])
      except (EOFError, ValueError) as e:
        raise PdfError(str(e)) from e
      if n != num:
        raise PdfError("object number mismatch")
      if self.crypt and num != self._enc_num:
        if isinstance(obj, Stream):
          obj.dict = self.crypt.decrypt_obj(obj.dict, num, g)
          obj.need_decrypt = self.resolve_plain(obj.dict.get("Type")) != "XRef"
        else:
          obj = self.crypt.decrypt_obj(obj, num, g)
      return obj
    data, first, pairs = self._objstm_entries(ent[1])
    idx = ent[2]
    if not (idx < len(pairs) and pairs[idx][0] == num):
      idx = next((i for i, (a, _) in enumerate(pairs) if a == num), None)
      if idx is None:
        raise PdfError("object not in object stream")
    try:
      o = Lexer(data, first + pairs[idx][1]).parse()
    except EOFError:
      return None
    return None if isinstance(o, Keyword) else o

  @staticmethod
  def resolve_plain(o):
    return o if not isinstance(o, Ref) else None

  def resolve(self, o):
    for _ in range(32):
      if not isinstance(o, Ref):
        return o
      o = self.get(o.num)
    return None

  def object_numbers(self):
    return sorted(self.xref)


# ======================================================================
# PDF functions (needed for Separation / DeviceN tint transforms)
# ======================================================================


def _ps_parse(tokens):
  prog = []
  for t in tokens:
    if t == "{":
      prog.append(_ps_parse(tokens))
    elif t == "}":
      return prog
    else:
      prog.append(t)
  return prog


def _ps_run(prog, st):
  i = 0
  n = len(prog)
  while i < n:
    t = prog[i]
    i += 1
    if isinstance(t, list):
      nxt = prog[i] if i < n else None
      if nxt == "if":
        i += 1
        if st.pop():
          _ps_run(t, st)
      elif isinstance(nxt, list) and i + 1 < n and prog[i + 1] == "ifelse":
        cond = st.pop()
        _ps_run(t if cond else nxt, st)
        i += 2
      continue
    try:
      st.append(float(t) if any(c in t for c in ".eE") else int(t))
      continue
    except ValueError:
      pass
    if t == "add":
      b = st.pop()
      st[-1] += b
    elif t == "sub":
      b = st.pop()
      st[-1] -= b
    elif t == "mul":
      b = st.pop()
      st[-1] *= b
    elif t == "div":
      b = st.pop()
      st[-1] = st[-1] / b if b else 0.0
    elif t == "idiv":
      b = st.pop()
      st[-1] = int(st[-1] / b) if b else 0
    elif t == "mod":
      b = st.pop()
      st[-1] = int(math.fmod(st[-1], b)) if b else 0
    elif t == "neg":
      st[-1] = -st[-1]
    elif t == "abs":
      st[-1] = abs(st[-1])
    elif t == "ceiling":
      st[-1] = math.ceil(st[-1])
    elif t == "floor":
      st[-1] = math.floor(st[-1])
    elif t == "round":
      st[-1] = math.floor(st[-1] + 0.5)
    elif t == "truncate":
      st[-1] = math.trunc(st[-1])
    elif t == "sqrt":
      st[-1] = math.sqrt(max(st[-1], 0))
    elif t == "sin":
      st[-1] = math.sin(math.radians(st[-1]))
    elif t == "cos":
      st[-1] = math.cos(math.radians(st[-1]))
    elif t == "atan":
      den = st.pop()
      num = st.pop()
      st.append(math.degrees(math.atan2(num, den)) % 360)
    elif t == "exp":
      e = st.pop()
      b = st.pop()
      try:
        st.append(float(b) ** e)
      except ValueError, ZeroDivisionError, OverflowError:
        st.append(0.0)
    elif t == "ln":
      st[-1] = math.log(st[-1]) if st[-1] > 0 else 0.0
    elif t == "log":
      st[-1] = math.log10(st[-1]) if st[-1] > 0 else 0.0
    elif t == "cvi":
      st[-1] = int(st[-1])
    elif t == "cvr":
      st[-1] = float(st[-1])
    elif t in ("eq", "ne", "gt", "ge", "lt", "le"):
      b = st.pop()
      a = st.pop()
      st.append(
        {
          "eq": a == b,
          "ne": a != b,
          "gt": a > b,
          "ge": a >= b,
          "lt": a < b,
          "le": a <= b,
        }[t]
      )
    elif t in ("and", "or", "xor"):
      b = st.pop()
      a = st.pop()
      st.append({"and": a & b, "or": a | b, "xor": a ^ b}[t])
    elif t == "not":
      a = st.pop()
      st.append((not a) if isinstance(a, bool) else ~a)
    elif t == "bitshift":
      s = st.pop()
      a = st.pop()
      st.append(a << s if s >= 0 else a >> -s)
    elif t == "true":
      st.append(True)
    elif t == "false":
      st.append(False)
    elif t == "pop":
      st.pop()
    elif t == "exch":
      st[-1], st[-2] = st[-2], st[-1]
    elif t == "dup":
      st.append(st[-1])
    elif t == "copy":
      c = int(st.pop())
      if c > 0:
        st.extend(st[-c:])
    elif t == "index":
      k = int(st.pop())
      st.append(st[-1 - k])
    elif t == "roll":
      j = int(st.pop())
      c = int(st.pop())
      if c > 0:
        j %= c
        if j:
          seg = st[-c:]
          st[-c:] = seg[-j:] + seg[:-j]


def make_function(doc, obj, depth=0):
  """Return f(list_of_floats) -> list_of_floats for PDF function types 0, 2, 3, 4."""
  r = doc.resolve
  if depth > 8:
    raise PdfError("function nesting too deep")
  o = r(obj)
  if isinstance(o, list):
    fs = [make_function(doc, x, depth + 1) for x in o]
    return lambda xs: [f(xs)[0] for f in fs]
  d = o.dict if isinstance(o, Stream) else o
  if not isinstance(d, dict):
    raise PdfError("bad function")
  ft = r(d.get("FunctionType"))

  def nums(key, default=None):
    v = r(d.get(key))
    return [float(r(x)) for x in v] if isinstance(v, list) else default

  domain = nums("Domain", [0.0, 1.0])
  rng = nums("Range")

  def clip_in(xs):
    return [
      min(max(x, domain[2 * i]), domain[2 * i + 1])
      for i, x in enumerate(xs[: len(domain) // 2])
    ]

  def clip_out(ys):
    if rng:
      return [
        min(max(y, rng[2 * i]), rng[2 * i + 1])
        for i, y in enumerate(ys[: len(rng) // 2])
      ]
    return list(ys)

  if ft == 2:
    c0 = nums("C0", [0.0])
    c1 = nums("C1", [1.0])
    n = float(r(d.get("N", 1)))

    def f2(xs):
      x = clip_in(xs)[0]
      try:
        t = x**n if x >= 0 else 0.0
      except ZeroDivisionError, OverflowError:
        t = 0.0
      return clip_out([a + t * (b - a) for a, b in zip(c0, c1)])

    return f2
  if ft == 3:
    fns = [make_function(doc, x, depth + 1) for x in r(d["Functions"])]
    bounds = nums("Bounds", [])
    enc = nums("Encode")

    def f3(xs):
      x = clip_in(xs)[0]
      k = len(fns)
      i = 0
      while i < k - 1 and x >= bounds[i]:
        i += 1
      lo = domain[0] if i == 0 else bounds[i - 1]
      hi = domain[1] if i == k - 1 else bounds[i]
      e0, e1 = enc[2 * i], enc[2 * i + 1]
      xx = e0 if hi == lo else e0 + (x - lo) * (e1 - e0) / (hi - lo)
      return clip_out(fns[i]([xx]))

    return f3
  if ft == 0:
    size = [int(v) for v in nums("Size")]
    bps = int(r(d["BitsPerSample"]))
    m = len(size)
    n_out = len(rng) // 2
    enc = nums("Encode") or [v for s in size for v in (0, s - 1)]
    dec = nums("Decode") or rng
    raw, _, _ = decode_stream(doc, o)
    total = n_out * math.prod(size)
    if bps % 8 == 0:
      step = bps // 8
      samples = [
        int.from_bytes(raw[i * step : (i + 1) * step], "big") for i in range(total)
      ]
    else:
      big = int.from_bytes(raw, "big")
      nbits = len(raw) * 8
      mask = (1 << bps) - 1
      samples = [
        ((big >> (nbits - (i + 1) * bps)) & mask) if (i + 1) * bps <= nbits else 0
        for i in range(total)
      ]
    samples += [0] * (total - len(samples))
    strides = []
    acc = n_out
    for s in size:
      strides.append(acc)
      acc *= s
    maxs = float((1 << bps) - 1)

    def f0(xs):
      xs = clip_in(xs)
      es = []
      for i, x in enumerate(xs):
        d0, d1 = domain[2 * i], domain[2 * i + 1]
        e0, e1 = enc[2 * i], enc[2 * i + 1]
        e = e0 if d1 == d0 else e0 + (x - d0) * (e1 - e0) / (d1 - d0)
        es.append(min(max(e, 0.0), size[i] - 1))
      base = [math.floor(e) for e in es]
      frac = [e - b for e, b in zip(es, base)]
      out = [0.0] * n_out
      for corner in range(1 << m):
        wgt = 1.0
        off = 0
        for i in range(m):
          bit = (corner >> i) & 1
          idx = min(base[i] + bit, size[i] - 1)
          wgt *= frac[i] if bit else 1.0 - frac[i]
          off += idx * strides[i]
        if wgt:
          for j in range(n_out):
            out[j] += wgt * samples[off + j]
      return clip_out(
        [
          dec[2 * j] + out[j] * (dec[2 * j + 1] - dec[2 * j]) / maxs
          for j in range(n_out)
        ]
      )

    return f0
  if ft == 4:
    raw, _, _ = decode_stream(doc, o)
    toks = iter(re.findall(r"[{}]|[^\s{}]+", raw.decode("latin-1")))
    next(toks, None)  # leading "{"
    prog = _ps_parse(toks)
    n_out = len(rng) // 2

    def f4(xs):
      st = list(clip_in(xs))
      _ps_run(prog, st)
      return clip_out([float(v) for v in st[-n_out:]])

    return f4
  raise PdfError(f"unsupported function type {ft!r}")


# ======================================================================
# Colour spaces
# ======================================================================


def _b(x):
  return 0 if x <= 0 else 255 if x >= 1 else int(x * 255 + 0.5)


class ColorSpace:
  def __init__(
    self,
    kind,
    n,
    base=None,
    hival=0,
    lookup=b"",
    func=None,
    wp=(0.9642, 1.0, 0.8249),
    rng=(-100.0, 100.0, -100.0, 100.0),
  ):
    self.kind, self.n, self.base, self.hival, self.lookup = kind, n, base, hival, lookup
    self.func, self.wp, self.rng = func, wp, rng
    self._pal = None

  def default_decode(self, bpc):
    if self.kind == "indexed":
      return [0.0, float((1 << bpc) - 1)]
    if self.kind == "lab":
      return [0.0, 100.0] + list(self.rng)
    return [0.0, 1.0] * self.n

  def scale_bytes(self, bs):
    """Map 0..255 sample bytes onto this space's natural component ranges."""
    if self.kind == "lab":
      r = self.rng
      return (
        bs[0] / 255 * 100,
        r[0] + bs[1] / 255 * (r[1] - r[0]),
        r[2] + bs[2] / 255 * (r[3] - r[2]),
      )
    return tuple(v / 255 for v in bs)

  def to_rgb(self, c):
    k = self.kind
    if k == "gray":
      g = _b(c[0])
      return (g, g, g)
    if k == "rgb":
      return (_b(c[0]), _b(c[1]), _b(c[2]))
    if k == "cmyk":
      cc, mm, yy, kk = (min(max(v, 0.0), 1.0) for v in c[:4])
      return (_b((1 - cc) * (1 - kk)), _b((1 - mm) * (1 - kk)), _b((1 - yy) * (1 - kk)))
    if k == "lab":
      L, a, b = c[:3]
      fy = (L + 16) / 116
      fx = fy + a / 500
      fz = fy - b / 200

      def g(t):
        return t**3 if t > 6 / 29 else 3 * (6 / 29) ** 2 * (t - 4 / 29)

      X, Y, Z = self.wp[0] * g(fx), self.wp[1] * g(fy), self.wp[2] * g(fz)
      lin = (
        3.1338561 * X - 1.6168667 * Y - 0.4906146 * Z,
        -0.9787684 * X + 1.9161415 * Y + 0.0334540 * Z,
        0.0719453 * X - 0.2289914 * Y + 1.4052427 * Z,
      )
      return tuple(
        _b(12.92 * v if v <= 0.0031308 else 1.055 * max(v, 0) ** (1 / 2.4) - 0.055)
        for v in lin
      )
    if k == "tint":
      if self.func is None:
        g = _b(1 - c[0])
        return (g, g, g)
      return self.base.to_rgb(self.func(list(c)))
    if k == "indexed":
      pal = self.palette()
      return pal[min(max(int(c[0]), 0), len(pal) - 1)]
    raise PdfError("bad colour space")

  def palette(self):
    if self._pal is None:
      bn = self.base.n
      pal = []
      for i in range(self.hival + 1):
        ent = self.lookup[i * bn : (i + 1) * bn]
        ent = ent + bytes(bn - len(ent))
        pal.append(self.base.to_rgb(self.base.scale_bytes(tuple(ent))))
      self._pal = pal or [(0, 0, 0)]
    return self._pal


_GRAY, _RGB, _CMYK = ColorSpace("gray", 1), ColorSpace("rgb", 3), ColorSpace("cmyk", 4)
_DEVICE_NAMES = {
  "DeviceGray": _GRAY,
  "G": _GRAY,
  "CalGray": _GRAY,
  "DeviceRGB": _RGB,
  "RGB": _RGB,
  "CalRGB": _RGB,
  "DeviceCMYK": _CMYK,
  "CMYK": _CMYK,
}


def parse_cs(doc, obj, res=None, depth=0):
  r = doc.resolve
  if depth > 8:
    raise PdfError("colour space nesting too deep")
  o = r(obj)
  if isinstance(o, Name):
    if str(o) in _DEVICE_NAMES:
      return _DEVICE_NAMES[str(o)]
    csd = (
      r(r(res).get("ColorSpace"))
      if res is not None and isinstance(r(res), dict)
      else None
    )
    if isinstance(csd, dict) and o in csd:
      return parse_cs(doc, csd[o], res, depth + 1)
    raise PdfError(f"unknown colour space /{o}")
  if not (isinstance(o, list) and o):
    raise PdfError("bad colour space")
  t = str(r(o[0]))
  if t in _DEVICE_NAMES:
    return _DEVICE_NAMES[t]
  if t == "ICCBased":
    st = r(o[1])
    n = int(r(st.dict.get("N", 0)) or 0)
    if n in (1, 3, 4):
      return {1: _GRAY, 3: _RGB, 4: _CMYK}[n]
    return parse_cs(doc, st.dict.get("Alternate"), res, depth + 1)
  if t in ("Indexed", "I"):
    base = parse_cs(doc, o[1], res, depth + 1)
    lk = r(o[3])
    if isinstance(lk, Stream):
      lk = decode_stream(doc, lk)[0]
    if not isinstance(lk, bytes):
      lk = b""
    return ColorSpace(
      "indexed", 1, base=base, hival=min(max(int(r(o[2])), 0), 255), lookup=lk
    )
  if t == "Lab":
    d = r(o[1]) or {}
    wp = [float(r(x)) for x in (r(d.get("WhitePoint")) or [0.9642, 1.0, 0.8249])]
    rg = [float(r(x)) for x in (r(d.get("Range")) or [-100, 100, -100, 100])]
    return ColorSpace("lab", 3, wp=tuple(wp), rng=tuple(rg))
  if t in ("Separation", "DeviceN"):
    names = r(o[1])
    n = len(names) if t == "DeviceN" and isinstance(names, list) else 1
    alt = parse_cs(doc, o[2], res, depth + 1)
    try:
      fn = make_function(doc, o[3])
    except Exception:  # noqa: BLE001
      fn = None
    return ColorSpace("tint", n, base=alt, func=fn)
  raise PdfError(f"unsupported colour space {t}")


# ======================================================================
# Image encoding helpers (PNG / TIFF / JBIG2 containers)
# ======================================================================

_INVERT = bytes(255 - i for i in range(256))


def _png_chunk(tag, body):
  return (
    struct.pack(">I", len(body))
    + tag
    + body
    + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
  )


def png_bytes(w, h, ctype, depth, data, palette=None):
  channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
  rl = (w * channels * depth + 7) // 8
  if len(data) < rl * h:
    data = data + bytes(rl * h - len(data))
  raw = b"".join([b"\x00" + data[y * rl : (y + 1) * rl] for y in range(h)])
  out = b"\x89PNG\r\n\x1a\n" + _png_chunk(
    b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ctype, 0, 0, 0)
  )
  if palette:
    out += _png_chunk(b"PLTE", palette)
  return out + _png_chunk(b"IDAT", zlib.compress(raw, 6)) + _png_chunk(b"IEND", b"")


def tiff_ccitt(data, cols, rows, k, photometric, byte_align=False):
  """Wrap raw CCITT G3/G4 data in a minimal single-strip TIFF."""
  comp = 4 if k < 0 else 3
  ents = [
    (256, 4, cols),
    (257, 4, rows),
    (258, 3, 1),
    (259, 3, comp),
    (262, 3, photometric),
    (266, 3, 1),
    (273, 4, 0),
    (277, 3, 1),
    (278, 4, rows),
    (279, 4, len(data)),
  ]
  if comp == 3:
    ents.append((292, 4, (1 if k > 0 else 0) | (4 if byte_align else 0)))
  else:
    ents.append((293, 4, 0))
  ents.sort()
  data_off = 8 + 2 + 12 * len(ents) + 4
  ifd = struct.pack("<H", len(ents))
  for tag, typ, val in ents:
    if tag == 273:
      val = data_off
    ifd += struct.pack("<HHI", tag, typ, 1) + (
      struct.pack("<HH", val, 0) if typ == 3 else struct.pack("<I", val)
    )
  return b"II*\x00" + struct.pack("<I", 8) + ifd + struct.pack("<I", 0) + data


def _jpeg_info(data):
  i = 2
  n = len(data)
  while i + 4 <= n:
    if data[i] != 0xFF:
      i += 1
      continue
    m = data[i + 1]
    if m == 0xFF:
      i += 1
      continue
    if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
      i += 2
      continue
    if m in (0xD9, 0xDA):
      break
    ln = struct.unpack(">H", data[i + 2 : i + 4])[0]
    if m in (
      0xC0,
      0xC1,
      0xC2,
      0xC3,
      0xC5,
      0xC6,
      0xC7,
      0xC9,
      0xCA,
      0xCB,
      0xCD,
      0xCE,
      0xCF,
    ):
      _, h, w, nc = struct.unpack(">BHHB", data[i + 4 : i + 10])
      return w, h, nc
    i += 2 + ln
  return None


# ======================================================================
# Raster conversion (anything that is not JPEG/JPX/CCITT/JBIG2) -> PNG
# ======================================================================

_EXPAND = {}


def _unpack_samples(data, w, h, n, bpc):
  """Return one byte per sample (value range 0..2^bpc-1, 16-bit reduced to 8)."""
  if bpc == 8:
    return data
  if bpc == 16:
    return data[0::2]
  if bpc not in (1, 2, 4):
    raise PdfError(f"unsupported bits per component {bpc}")
  t = _EXPAND.get(bpc)
  if t is None:
    per = 8 // bpc
    mask = (1 << bpc) - 1
    t = _EXPAND[bpc] = [
      bytes(((b >> (8 - bpc * (i + 1))) & mask) for i in range(per)) for b in range(256)
    ]
  rl = (w * n * bpc + 7) // 8
  cnt = w * n
  return b"".join(
    [b"".join(map(t.__getitem__, data[y * rl : (y + 1) * rl]))[:cnt] for y in range(h)]
  )


def _lut(dmin, dmax, maxv):
  return bytes(_b(dmin + (dmax - dmin) * min(v, maxv) / maxv) for v in range(256))


def _resize_plane(plane, w1, h1, w2, h2):
  if (w1, h1) == (w2, h2):
    return plane
  xs = [x * w1 // w2 for x in range(w2)]
  rows = []
  for y in range(h2):
    row = plane[(y * h1 // h2) * w1 : (y * h1 // h2 + 1) * w1]
    rows.append(bytes([row[x] for x in xs]))
  return b"".join(rows)


def _decoded_dict(doc, st):
  r = doc.resolve
  d = st.dict
  w, h = int(r(d.get("Width"))), int(r(d.get("Height")))
  if w <= 0 or h <= 0 or w * h > 600_000_000:
    raise PdfError(f"bad image size {w}x{h}")
  dec = r(d.get("Decode"))
  dec = [float(r(x)) for x in dec] if isinstance(dec, list) and dec else None
  return w, h, dec


def _gray_plane(doc, st):
  """Decode a (soft-)mask image to an 8-bit gray plane.  Returns (w, h, plane)."""
  r = doc.resolve
  w, h, dec = _decoded_dict(doc, st)
  data, imgf, _ = decode_stream(doc, st)
  if imgf:
    raise PdfError(f"mask uses {imgf}")
  bpc = int(r(st.dict.get("BitsPerComponent", 1 if r(st.dict.get("ImageMask")) else 8)))
  need = ((w * bpc + 7) // 8) * h
  data = data[:need].ljust(need, b"\x00")
  plane = _unpack_samples(data, w, h, 1, bpc)
  maxv = (1 << min(bpc, 8)) - 1
  d0, d1 = (dec[0], dec[1]) if dec else (0.0, 1.0)
  return w, h, plane.translate(_lut(d0, d1, maxv))


def _alpha_plane(doc, st, w, h, planes, bpc, n):
  """Build an 8-bit alpha plane from /SMask or /Mask.  Returns (alpha, mask_obj_num_or_None)."""
  r = doc.resolve
  d = st.dict
  sm = r(d.get("SMask"))
  if isinstance(sm, Stream):
    mw, mh, plane = _gray_plane(doc, sm)
    num = d["SMask"].num if isinstance(d.get("SMask"), Ref) else None
    return _resize_plane(plane, mw, mh, w, h), num
  mk = r(d.get("Mask"))
  if isinstance(mk, Stream):
    mw, mh, dec = _decoded_dict(doc, mk)
    data, imgf, _ = decode_stream(doc, mk)
    if imgf:
      raise PdfError(f"mask uses {imgf}")
    need = ((mw + 7) // 8) * mh
    plane = _unpack_samples(data[:need].ljust(need, b"\x00"), mw, mh, 1, 1)
    paint = 1 if dec and dec[0] == 1 else 0  # sample value that means "opaque"
    table = bytearray(256)
    table[paint] = 255
    num = d["Mask"].num if isinstance(d.get("Mask"), Ref) else None
    return _resize_plane(plane.translate(bytes(table)), mw, mh, w, h), num
  if isinstance(mk, list) and len(mk) >= 2 * n:
    rngs = [(int(r(mk[2 * i])), int(r(mk[2 * i + 1]))) for i in range(n)]
    if bpc == 16:
      rngs = [(a >> 8, b >> 8) for a, b in rngs]
    if n == 1:
      lo, hi = rngs[0]
      return planes[0].translate(
        bytes(0 if lo <= v <= hi else 255 for v in range(256))
      ), None
    hit = [
      bytes(1 if lo <= v <= hi else 0 for v in p) for p, (lo, hi) in zip(planes, rngs)
    ]
    return bytes([0 if all(t) else 255 for t in zip(*hit)]), None
  return None, None


def _interleave(chans):
  n = len(chans)
  if n == 1:
    return bytes(chans[0])
  out = bytearray(n * len(chans[0]))
  for i, c in enumerate(chans):
    out[i::n] = c
  return bytes(out)


def export_raster(doc, st, res=None):
  """Convert a raw-sample image to PNG.  Returns (png_bytes, w, h, merged_mask_obj_or_None, note)."""
  r = doc.resolve
  d = st.dict
  w, h, dec = _decoded_dict(doc, st)
  data, imgf, _ = decode_stream(doc, st)
  if imgf:
    raise PdfError(f"internal: {imgf} is not raster")
  is_mask = bool(r(d.get("ImageMask")))
  bpc = 1 if is_mask else int(r(d.get("BitsPerComponent", 8)))
  cs = None if is_mask else parse_cs(doc, d.get("ColorSpace"), res)
  n = 1 if is_mask else cs.n
  need = ((w * n * bpc + 7) // 8) * h
  note = ""
  if len(data) < need:
    note = f"data truncated ({len(data)} of {need} bytes)"
    data = data.ljust(need, b"\x00")
  data = data[:need]
  default = cs.default_decode(bpc) if cs else [0.0, 1.0]
  is_default = dec is None or dec == default
  is_inverted = (
    dec is not None
    and len(dec) == 2 * n
    and all(dec[2 * i] == 1 and dec[2 * i + 1] == 0 for i in range(n))
  )
  # --- stencil masks: 1-bit gray, painted pixels (sample 0) black
  if is_mask:
    mdata = data.translate(_INVERT) if dec and dec[0] == 1 else data
    return png_bytes(w, h, 0, 1, mdata), w, h, None, note
  has_mask = isinstance(r(d.get("SMask")), Stream) or isinstance(
    r(d.get("Mask")), (Stream, list)
  )
  # --- fast paths: sample data can be handed straight to the PNG encoder
  if not has_mask and (is_default or is_inverted):
    pix = data.translate(_INVERT) if (is_inverted and not is_default) else data
    if cs.kind == "gray" and bpc in (1, 2, 4, 8, 16):
      return png_bytes(w, h, 0, bpc, pix), w, h, None, note
    if cs.kind == "rgb" and bpc in (8, 16):
      return png_bytes(w, h, 2, bpc, pix), w, h, None, note
    if cs.kind == "indexed" and is_default and bpc in (1, 2, 4, 8):
      pal = cs.palette() + [(0, 0, 0)] * ((1 << bpc) - len(cs.palette()))
      return (
        png_bytes(w, h, 3, bpc, data, b"".join(bytes(c) for c in pal[: 1 << bpc])),
        w,
        h,
        None,
        note,
      )
  # --- general path: expand to one byte per sample, convert to 8-bit gray / RGB
  flat = _unpack_samples(data, w, h, n, bpc)
  raw_planes = [flat] if n == 1 else [flat[i::n] for i in range(n)]
  maxv = (1 << min(bpc, 8)) - 1
  dd = dec if dec and len(dec) >= 2 * n else default
  pairs = [(dd[2 * i], dd[2 * i + 1]) for i in range(n)]
  k = cs.kind
  if k == "gray":
    mode, chans = "L", [raw_planes[0].translate(_lut(*pairs[0], maxv))]
  elif k == "rgb":
    mode, chans = (
      "RGB",
      [p.translate(_lut(*pr, maxv)) for p, pr in zip(raw_planes, pairs)],
    )
  elif k == "cmyk":
    C, M, Y, K = [p.translate(_lut(*pr, maxv)) for p, pr in zip(raw_planes, pairs)]
    mode = "RGB"
    chans = [
      bytes([(255 - a) * (255 - c) // 255 for a, c in zip(P, K)]) for P in (C, M, Y)
    ]
  elif k == "indexed":
    pal = cs.palette()
    d0, d1 = pairs[0]
    tabs = [bytearray(256) for _ in range(3)]
    for v in range(256):
      idx = round(d0 + (d1 - d0) * min(v, maxv) / maxv)
      rgb = pal[min(max(idx, 0), len(pal) - 1)]
      for c in range(3):
        tabs[c][v] = rgb[c]
    mode, chans = "RGB", [raw_planes[0].translate(bytes(t)) for t in tabs]
  else:  # Lab, Separation, DeviceN
    mode = "RGB"
    if n == 1:
      d0, d1 = pairs[0]
      rgbs = [cs.to_rgb((d0 + (d1 - d0) * min(v, maxv) / maxv,)) for v in range(256)]
      chans = [raw_planes[0].translate(bytes(t[c] for t in rgbs)) for c in range(3)]
    else:
      cache = {}
      npx = w * h
      chans = [bytearray(npx), bytearray(npx), bytearray(npx)]
      for i, tup in enumerate(zip(*raw_planes)):
        rgb = cache.get(tup)
        if rgb is None:
          comps = tuple(
            a + (b - a) * min(v, maxv) / maxv for (a, b), v in zip(pairs, tup)
          )
          rgb = cache[tup] = cs.to_rgb(comps)
        chans[0][i], chans[1][i], chans[2][i] = rgb
  alpha, mask_num = (None, None)
  if has_mask:
    try:
      alpha, mask_num = _alpha_plane(doc, st, w, h, raw_planes, bpc, n)
    except PdfError as e:
      note = (note + "; " if note else "") + f"mask ignored: {e}"
  if alpha is not None:
    chans = list(chans) + [alpha]
  ctype = {("L", 1): 0, ("L", 2): 4, ("RGB", 3): 2, ("RGB", 4): 6}[(mode, len(chans))]
  return png_bytes(w, h, ctype, 8, _interleave(chans)), w, h, mask_num, note


# ======================================================================
# Image extraction (XObjects + inline images)
# ======================================================================


@dataclass
class ExtractedImage:
  data: bytes
  ext: str
  width: int
  height: int
  obj: int | None = None
  pages: list = field(default_factory=list)
  inline: bool = False
  is_mask: bool = False
  note: str = ""

  @property
  def page(self):
    return self.pages[0] if self.pages else 0


def _get_jbig2_globals(doc, parms):
  g = parms.get("JBIG2Globals")
  return decode_stream(doc, g)[0] if isinstance(g, Stream) else b""


def export_image(doc, st, res=None):
  """Export one image stream.  Returns (ExtractedImage, merged_mask_obj_or_None)."""
  r = doc.resolve
  d = st.dict
  w, h = int(r(d.get("Width", 0)) or 0), int(r(d.get("Height", 0)) or 0)
  data, imgf, parms = decode_stream(doc, st)
  if not data and imgf != "JBIG2Decode":
    raise PdfError("empty image stream")
  if imgf is None:
    png, w, h, mnum, note = export_raster(doc, st, res)
    return ExtractedImage(png, "png", w, h, note=note), mnum
  if imgf == "DCTDecode":
    s = data.find(b"\xff\xd8")
    if s > 0:
      data = data[s:]
    info = _jpeg_info(data)
    note = ""
    if info:
      w, h = info[0], info[1]
      if info[2] == 4:
        note = "CMYK JPEG (colours may look inverted in some viewers)"
    return ExtractedImage(data, "jpg", w, h, note=note), None
  if imgf == "JPXDecode":
    ext = "j2k" if data[:2] == b"\xff\x4f" else "jp2"
    return ExtractedImage(data, ext, w, h), None
  if imgf == "JBIG2Decode":
    body = b"\x97JB2\r\n\x1a\n" + b"\x03" + _get_jbig2_globals(doc, parms) + data
    return ExtractedImage(body, "jb2", w, h, note="JBIG2 (decode with jbig2dec)"), None
  if imgf == "CCITTFaxDecode":
    k = int(parms.get("K", 0) or 0)
    cols = int(parms.get("Columns", 1728) or 1728)
    rows = int(parms.get("Rows", 0) or 0) or h
    black_is1 = bool(parms.get("BlackIs1", False))
    dec = r(d.get("Decode"))
    dec_inv = isinstance(dec, list) and len(dec) >= 2 and r(dec[0]) == 1
    # Black runs decode to 1 bits (BlackIs1) or 0 bits; /Decode may invert that again.  The TIFF
    # photometric tag (1 = 0 is black) must make black runs display black exactly when both agree.
    photometric = 1 if (black_is1 == dec_inv) else 0
    align = bool(parms.get("EncodedByteAlign", False))
    note = "CCITT G4" if k < 0 else "CCITT G3"
    if align and k < 0:
      note += " (byte-aligned rows: TIFF cannot express this, output may be skewed)"
    return ExtractedImage(
      tiff_ccitt(data, cols, rows, k, photometric, align), "tiff", cols, rows, note=note
    ), None
  raise PdfError("unsupported image filter " + str(imgf))


_INLINE_KEYS = {
  "BPC": "BitsPerComponent",
  "CS": "ColorSpace",
  "D": "Decode",
  "DP": "DecodeParms",
  "F": "Filter",
  "H": "Height",
  "IM": "ImageMask",
  "I": "Interpolate",
  "W": "Width",
  "L": "Length",
}
_INLINE_CS = {
  "G": "DeviceGray",
  "RGB": "DeviceRGB",
  "CMYK": "DeviceCMYK",
  "I": "Indexed",
}
_INLINE_START = re.compile(rb"(?<![A-Za-z0-9_.*'\"])BI(?=[\x00\t\n\x0c\r /])")
_EI = re.compile(rb"(?<=[\x00\t\n\x0c\r ])EI(?=[\x00\t\n\x0c\r ]|$)")


def _inline_norm(d, resources, doc):
  out = {}
  for k, v in d.items():
    out[Name(_INLINE_KEYS.get(str(k), str(k)))] = v

  def cs_fix(v, depth=0):
    if isinstance(v, Name) and str(v) in _INLINE_CS:
      return Name(_INLINE_CS[str(v)])
    if isinstance(v, list):
      return [cs_fix(x, depth + 1) if i < 2 else x for i, x in enumerate(v)]
    return v

  cs = out.get("ColorSpace")
  if cs is not None:
    cs = cs_fix(cs)
    if isinstance(cs, Name) and str(cs) not in _DEVICE_NAMES and resources is not None:
      csd = (
        doc.resolve(doc.resolve(resources).get("ColorSpace"))
        if isinstance(doc.resolve(resources), dict)
        else None
      )
      if isinstance(csd, dict) and cs in csd:
        cs = doc.resolve(csd[cs])
    out["ColorSpace"] = cs
  f = out.get("Filter")
  if f is not None:
    out["Filter"] = (
      [Name(_FILTER_ALIAS.get(str(x), str(x))) for x in f]
      if isinstance(f, list)
      else Name(_FILTER_ALIAS.get(str(f), str(f)))
    )
  return out


def scan_inline_images(doc, data, resources=None):
  """Yield Stream objects for every inline image (BI ... ID ... EI) in a content stream."""
  pos = 0
  while True:
    m = _INLINE_START.search(data, pos)
    if not m:
      return
    lx = Lexer(data, m.end(), refs=False)
    d = {}
    try:
      while True:
        k = lx.parse()
        if isinstance(k, Keyword):
          if k == "ID":
            break
          raise ValueError
        v = lx.parse()
        if not isinstance(k, Name) or isinstance(v, Keyword):
          raise TypeError
        d[k] = v
    except ValueError, TypeError, EOFError:
      pos = m.end()
      continue
    p = lx.pos
    if data.startswith(b"\r\n", p):
      p += 2
    elif p < len(data) and data[p] in _WS:
      p += 1
    d = _inline_norm(d, resources, doc)
    end = None
    try:  # unfiltered data has a computable length
      if d.get("Filter") is None:
        w, h = int(d["Width"]), int(d["Height"])
        if d.get("ImageMask") is True:
          n, bpc = 1, 1
        else:
          n = parse_cs(doc, d["ColorSpace"], resources).n
          bpc = int(d["BitsPerComponent"])
        length = ((w * n * bpc + 7) // 8) * h
        tail = data[p + length : p + length + 16].lstrip(b"\x00\t\n\x0c\r ")
        if tail.startswith(b"EI"):
          end = p + length
          ei_end = (
            p + length + (len(data[p + length : p + length + 16]) - len(tail)) + 2
          )
    except Exception:  # noqa: BLE001
      end = None
    if end is None:
      for cand in _EI.finditer(data, p):
        after = data[cand.end() : cand.end() + 12]
        if all(32 <= c < 127 or c in _WS for c in after):
          end, ei_end = cand.start(), cand.end()
          break
      else:
        pos = m.end()
        continue
    pos = ei_end
    yield Stream(d, data[p:end], doc)


def collect_pages(doc):
  """Return [(page_dict, inherited_resources), ...] in document order."""
  r = doc.resolve
  pages = []
  seen = set()

  def walk(ref, inherited):
    node = r(ref)
    key = ref.num if isinstance(ref, Ref) else id(node)
    if not isinstance(node, dict) or key in seen:
      return
    seen.add(key)
    res = node.get("Resources", inherited)
    kids = r(node.get("Kids"))
    if isinstance(kids, list) and r(node.get("Type")) != "Page":
      for k in kids:
        walk(k, res)
    else:
      pages.append((node, res))

  root = r(doc.trailer.get("Root"))
  if isinstance(root, dict):
    walk(root.get("Pages"), None)
  if not pages:  # broken page tree: collect every /Type /Page object
    for num in doc.object_numbers():
      try:
        o = doc.get(num)
      except Exception as e:  # noqa: BLE001
        doc.warn(f"object {num}: {e}")
        continue
      if isinstance(o, dict) and r(o.get("Type")) == "Page":
        pages.append((o, o.get("Resources")))
  return pages


class _Collector:
  """Walks pages, forms, patterns, Type3 fonts and annotations: records which page uses which
  image object and gathers inline images."""

  def __init__(self, doc, inline):
    self.doc = doc
    self.inline = inline
    self.image_pages = {}
    self.inline_images = []  # (page, Stream)
    self._scanned = set()

  def run(self):
    for pno, (node, res) in enumerate(collect_pages(self.doc), 1):
      try:
        self._page(pno, node, res)
      except Exception as e:  # noqa: BLE001
        self.doc.warn(f"page {pno}: {e}")

  def _content(self, x):
    try:
      st = self.doc.resolve(x)
      data, imgf, _ = decode_stream(self.doc, st)
      return b"" if imgf else data
    except Exception:  # noqa: BLE001
      return b""

  def _scan(self, data, res, pno):
    if b"BI" in data and b"EI" in data:
      for st in scan_inline_images(self.doc, data, res):
        self.inline_images.append((pno, st))

  def _page(self, pno, node, res):
    r = self.doc.resolve
    visited = set()
    self._resources(res, pno, visited)
    if self.inline:
      c = r(node.get("Contents"))
      items = c if isinstance(c, list) else [node.get("Contents")]
      self._scan(b"\n".join(self._content(x) for x in items if x is not None), res, pno)
    for a in r(node.get("Annots")) or []:
      ad = r(a)
      ap = r(ad.get("AP")) if isinstance(ad, dict) else None
      if not isinstance(ap, dict):
        continue
      for key in ("N", "R", "D"):
        v = ap.get(key)
        rv = r(v)
        if isinstance(rv, Stream):
          self._form(v, res, pno, visited)
        elif isinstance(rv, dict):
          for sub in rv.values():
            if isinstance(r(sub), Stream):
              self._form(sub, res, pno, visited)

  def _form(self, x, parent_res, pno, visited):
    r = self.doc.resolve
    st = r(x)
    if not isinstance(st, Stream):
      return
    key = x.num if isinstance(x, Ref) else id(st)
    if key in visited:
      return
    visited.add(key)
    res = st.dict.get("Resources", parent_res)
    self._resources(res, pno, visited)
    if self.inline and key not in self._scanned:
      self._scanned.add(key)
      self._scan(self._content(x), res, pno)

  def _resources(self, res, pno, visited):
    r = self.doc.resolve
    res_d = r(res)
    if not isinstance(res_d, dict):
      return
    xo = r(res_d.get("XObject"))
    for ref in xo.values() if isinstance(xo, dict) else []:
      obj = r(ref)
      if not isinstance(obj, Stream):
        continue
      sub = r(obj.dict.get("Subtype"))
      if sub == "Image" and isinstance(ref, Ref):
        lst = self.image_pages.setdefault(ref.num, [])
        if pno not in lst:
          lst.append(pno)
      elif sub == "Form":
        self._form(ref, res, pno, visited)
    pat = r(res_d.get("Pattern"))
    for ref in pat.values() if isinstance(pat, dict) else []:
      if isinstance(r(ref), Stream):
        self._form(ref, res, pno, visited)
    egs = r(res_d.get("ExtGState"))
    for gs in egs.values() if isinstance(egs, dict) else []:
      gs = r(gs)
      sm = r(gs.get("SMask")) if isinstance(gs, dict) else None
      if isinstance(sm, dict) and isinstance(r(sm.get("G")), Stream):
        self._form(sm.get("G"), res, pno, visited)
    fonts = r(res_d.get("Font"))
    for f in fonts.values() if isinstance(fonts, dict) else []:
      fd = r(f)
      if isinstance(fd, dict) and r(fd.get("Subtype")) == "Type3":
        cp = r(fd.get("CharProcs"))
        for proc in cp.values() if isinstance(cp, dict) else []:
          if isinstance(r(proc), Stream):
            self._form(proc, fd.get("Resources", res), pno, visited)


class Extractor:
  def __init__(self, data, password="", include_inline=True, min_size=0, warn=None):
    self.warnings = []

    def _warn(msg):
      self.warnings.append(msg)
      if warn:
        warn(msg)

    self.warn = _warn
    self.doc = PdfDocument(data, password, _warn)
    self.include_inline = include_inline
    self.min_size = min_size

  def __iter__(self):
    return self.images()

  def images(self):
    doc = self.doc
    col = _Collector(doc, self.include_inline)
    col.run()
    image_nums = []
    masks = set()
    for num in doc.object_numbers():
      try:
        o = doc.get(num)
      except Exception as e:  # noqa: BLE001
        doc.warn(f"object {num}: {e}")
        continue
      if isinstance(o, Stream) and doc.resolve(o.dict.get("Subtype")) == "Image":
        image_nums.append(num)
        for key in ("SMask", "Mask"):
          v = o.dict.get(key)
          if isinstance(v, Ref):
            masks.add(v.num)
    merged = set()

    def first_page(n):
      return min(col.image_pages.get(n, [10**9]))

    regular = sorted(
      (n for n in image_nums if n not in masks or n in col.image_pages),
      key=lambda n: (first_page(n), n),
    )
    leftovers = sorted(n for n in image_nums if n in masks and n not in col.image_pages)

    def run(num, as_mask=False):
      try:
        st = doc.get(num)
        img, mnum = export_image(doc, st)
      except Exception as e:  # noqa: BLE001
        self.warn(f"object {num}: {e}")
        return None
      if mnum:
        merged.add(mnum)
      img.obj = num
      img.pages = list(col.image_pages.get(num, []))
      img.is_mask = as_mask
      if "truncated" in img.note or "mask ignored" in img.note:
        self.warn(f"object {num}: {img.note}")
      return img if min(img.width, img.height) >= self.min_size else None

    for num in regular:
      img = run(num)
      if img:
        yield img
    for num in leftovers:
      if num in merged:
        continue
      img = run(num, as_mask=True)
      if img:
        yield img
    for pno, st in col.inline_images:
      try:
        img, _ = export_image(doc, st, None)
      except Exception as e:  # noqa: BLE001
        self.warn(f"inline image on page {pno}: {e}")
        continue
      img.inline = True
      img.pages = [pno]
      if min(img.width, img.height) >= self.min_size:
        yield img


def extract_images(source, password="", include_inline=True, min_size=0, warn=None):
  """Yield ExtractedImage objects.  `source` is a path or the PDF's bytes."""
  if isinstance(source, (bytes, bytearray)):
    data = bytes(source)
  else:
    with open(source, "rb") as fh:
      data = fh.read()
  return Extractor(data, password, include_inline, min_size, warn).images()


# ======================================================================
# Command line
# ======================================================================


def main(argv=None):
  ap = argparse.ArgumentParser(
    description="Extract every image from a PDF (standard library only)."
  )
  ap.add_argument("pdf")
  ap.add_argument("-o", "--output", help="output directory (default: <pdfname>_images)")
  ap.add_argument("-p", "--password", default="", help="password (default: empty)")
  ap.add_argument(
    "--min-size",
    type=int,
    default=0,
    metavar="PX",
    help="skip images smaller than PX in either dimension",
  )
  ap.add_argument(
    "--no-inline", action="store_true", help="do not look for inline (BI/EI) images"
  )
  ap.add_argument(
    "--dedupe", action="store_true", help="skip byte-identical output files"
  )
  ap.add_argument(
    "--manifest", action="store_true", help="write manifest.json describing every image"
  )
  ap.add_argument("-q", "--quiet", action="store_true")
  a = ap.parse_args(argv)

  outdir = a.output or (os.path.splitext(os.path.basename(a.pdf))[0] + "_images")
  os.makedirs(outdir, exist_ok=True)

  def warn(msg):
    if not a.quiet:
      print("warning: " + msg, file=sys.stderr)

  try:
    with open(a.pdf, "rb") as fh:
      data = fh.read()
    ex = Extractor(data, a.password, not a.no_inline, a.min_size, warn)
  except (OSError, PdfError) as e:
    print(f"error: {e}", file=sys.stderr)
    return 1

  seen = set()
  manifest = []
  count = 0
  inline_k = 0
  for img in ex.images():
    if a.dedupe:
      h = hashlib.sha256(img.data).digest()
      if h in seen:
        continue
      seen.add(h)
    count += 1
    pg = f"p{img.page:03d}"
    if img.inline:
      inline_k += 1
      stem = f"{count:04d}_{pg}_inline{inline_k}"
    else:
      stem = f"{count:04d}_{pg if img.pages else 'p---'}_obj{img.obj}{'_mask' if img.is_mask else ''}"
    path = os.path.join(outdir, f"{stem}.{img.ext}")
    with open(path, "wb") as fh:
      fh.write(img.data)
    manifest.append(
      {
        "file": os.path.basename(path),
        "object": img.obj,
        "pages": img.pages,
        "width": img.width,
        "height": img.height,
        "format": img.ext,
        "inline": img.inline,
        "mask": img.is_mask,
        "note": img.note,
      }
    )
    if not a.quiet:
      note = f"  [{img.note}]" if img.note else ""
      print(
        f"{os.path.basename(path):<44} {img.width:>5}x{img.height:<5} {img.ext}{note}"
      )
  if a.manifest:
    with open(os.path.join(outdir, "manifest.json"), "w") as fh:
      json.dump(manifest, fh, indent=2)
  if not a.quiet:
    print(f"{count} image(s) written to {outdir}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
