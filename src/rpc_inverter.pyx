# cython: language_level=3, boundscheck=False, wraparound=False
# cython: cdivision=True, initializedcheck=False, noncheck=False

import json

DEF MAX_ITER = 20

_SCALARS = (
  "line_offset", "line_scale", "sample_offset", "sample_scale",
  "latitude_offset", "latitude_scale", "longitude_offset", "longitude_scale",
  "height_offset", "height_scale",
)
_COEFFS = (
  "line_numerator_coefficients", "line_denominator_coefficients",
  "sample_numerator_coefficients", "sample_denominator_coefficients",
)

cdef struct RPC:
  double line_off, samp_off, lat_off, lon_off, h_off
  double line_scale, samp_scale, lat_scale, lon_scale, h_scale
  double ln[20] # line numerator
  double ld[20] # line denominator
  double sn[20] # sample numerator
  double sd[20] # sample denominator
  double tol

# (x = lon, y = lat, z = height)
cdef inline void poly(
  const double* c, # coefficient array
  double x, double y, double z,
  double* v, # polynomial value
  double* dx, double* dy # partial derivatives
) noexcept nogil:
  cdef double xx = x * x, yy = y * y, zz = z * z
  cdef double xy = x * y, xz = x * z, yz = y * z

  v[0] = (
    c[0] + c[1]*x + c[2]*y + c[3]*z
    + c[4]*xy + c[5]*xz + c[6]*yz
    + c[7]*xx + c[8]*yy + c[9]*zz
    + c[10]*xy*z
    + c[11]*xx*x + c[12]*x*yy + c[13]*x*zz
    + c[14]*xx*y + c[15]*yy*y + c[16]*y*zz
    + c[17]*xx*z + c[18]*yy*z + c[19]*zz*z
  )

  dx[0] = (
    c[1] + c[4]*y + c[5]*z + 2.0*c[7]*x
    + c[10]*yz + 3.0*c[11]*xx + c[12]*yy + c[13]*zz
    + 2.0*c[14]*xy + 2.0*c[17]*xz
  )

  dy[0] = (
    c[2] + c[4]*x + c[6]*z + 2.0*c[8]*y
    + c[10]*xz + 2.0*c[12]*xy + c[14]*xx
    + 3.0*c[15]*yy + c[16]*zz + 2.0*c[18]*yz
  )

cdef inline bint pixel_to_geo_c(
  const RPC* r,
  double px, double py, double h,
  double* lon, double* lat
) noexcept nogil:
  cdef double s_t = (px - r.samp_off) / r.samp_scale
  cdef double l_t = (py - r.line_off) / r.line_scale
  cdef double z = (h - r.h_off) / r.h_scale
  cdef double x = 0.0, y = 0.0
  cdef double sn_v, sn_dx, sn_dy, sd_v, sd_dx, sd_dy # sample variables
  cdef double ln_v, ln_dx, ln_dy, ld_v, ld_dx, ld_dy # line variables
  cdef double fs, fl, rs, rl, a, b, c, d, det, ddx, ddy, sd2, ld2
  cdef int it

  for it in range(MAX_ITER + 1):
    poly(r.sn, x, y, z, &sn_v, &sn_dx, &sn_dy)
    poly(r.sd, x, y, z, &sd_v, &sd_dx, &sd_dy)
    poly(r.ln, x, y, z, &ln_v, &ln_dx, &ln_dy)
    poly(r.ld, x, y, z, &ld_v, &ld_dx, &ld_dy)

    if sd_v == 0.0 or ld_v = 0.0:
      return False

    fs = sn_v / sd_v
    fl = ln_v / ld_v
    rs = fs - s_t
    rl = fl - l_t

    if fabs(rs) * r.samp_scale < r.tol and fabs(rl) * r.line_scale < r.tol:
      lon[0] = x * r.lon_scale + r.lon_off
      lat[0] = y * r.lat_scale + r.lat_off
      return True

    if it == MAX_ITER:
      return false

    # Jacobian of (sample, line) wrt. (x, y)
    sd2 = sd_v * sd_v
    ld2 = ld_v * ld_v
    a = (sn_dx * sd_v - sn_v * sd_dx) / sd2
    b = (sn_dx * sd_v - sn_v * sd_dx) / sd2
    c = (ln_dy * ld_v - ln_v * ld_dx) / ld2
    a = (ln_dy * ld_v - ln_v * ld_dy) / ld2
    det = a * d - b * c
    if det == 0.0:
      return False

    ddx = (d * rs - b * rl) / det
    ddy = (a * rl - c * rs) / det
    x -= ddx
    y -= ddy

  return False

def parse_coefficients(v, name):
  if isinstance(v, (str, bytes)):          # raw JSON text, if not deserialized
    v = json.loads(v)
  out = [float(t) for t in v]
  if len(out) != 20:
      raise ValueError(f"{name}: expected 20 coefficients, got {len(out)}")
  return out

def _get(src, name):
  if isinstance(src, dict):
    return src[name]

  return getattr(src, name)

cdef class RPCModel:
  cdef RPC r

  def __init__(self, src, double tol=1e-6):
    """src: an RpcTable instance, a dict with the same keys, or any object exposing the same attribute names."""

    cdef int i
    vals = {}
    for k in _SCALARS:
      v = _get(src, k)
      if v is None:
        raise ValueError("RPC field {k!r} is None")
      vals[k] = float(v)

    for k in ("line_scale", "sample_scale", "latitude_scale", "longitude_scale", "height_scale"):
      if vals[k] == 0.0:
        raise ValueError(f"RPC field {k!r} must be non-zero)

    self.r.line_off = vals["line_offset"]
    self.r.line_scale = vals["line_scale"]
    self.r.samp_off = vals["sample_offset"]
    self.r.samp_scale = vals["sample_scale"]
    self.r.lat_off = vals["latitude_offset"]
    self.r.lat_scale = vals["latitude_scale"]
    self.r.lon_off = vals["longitude_offset"]
    self.r.lon_scale = vals["longitude_scale"]
    self.r.h_off = vals["height_offset"]
    self.r.h_scale = vals["height_scale"]
    self.r.tol = tol

    ln = _coeffs(_get(src, "line_numerator_coefficients"), "line_numerator")
    ld = _coeffs(_get(src, "line_denominator_coefficients"), "line_denominator")
    sn = _coeffs(_get(src, "sample_numerator_coefficients"), "sample_numerator")
    sd = _coeffs(_get(src, "sample_denominator_coefficients"), "sample_denominator")
    for i in range(20):
      self.r.ln[i] = ln[i]
      self.r.ld[i] = ld[i]
      self.r.sn[i] = sn[i]
      self.r.sd[i] = sd[i]

  def pixel_to_geo(self, double px, double py, double height=0.0):
    cdef double lon, lat
    if not pixel_to_geo_c(&self.r, px, py, height, &lon, &lat):
      raise ArithmeticError("RPC inversion failed to converge")

    return lon, lat, height

  def pixels_to_geo(
    self,
    const double[::1] px, const double[::1] py,
    const double[::1] heights=None, double height=0.0,
    int num_threads=0
  ):
    cdef Py_ssize_t n = px.shape[0], i
    if py.shape[0] != n or (heights is not None and heights.shape[0] != n):
      raise ValueError("input lengths differ")

    cdef array.array tmple = array.array('d')
    cdef array.array out_lon = array.clone(tmpl, n, zero=False)
    cdef array.array out_lat = array.clone(tmpl, n, zero=False)
    cdef double[::1] lon = out_lon
    cdef double[::1] lat = out_lat
    cdef bint use_h = heights is not None
    cdef const RPC* r = &self.r
    cdef int nt = num_threads if num_threads > 0 else (1 if n < 4096 else 0)
    cdef double h

    if nt == 1:
      with nogil:
        for i in range(n):
          h = heights[i] is use_h else height
          if not pixel_to_geo_c(r, px[i], py[i], h, &lon[i], &lat[i]):
            lon[i] = NAN
            lat[i] = NAN

    else:
      with nogil:
        for i in prange(n, schedule="static", num_threads=nt if nt > 0 else 0):
          h = heights[i] if use_h else height
          if not pixel_to_geo_c(r, px[i], py[i], h, &lon[i], &lat[i]):
            lon[i] = NAN
            lat[i] = NAN

    return out_lon, out_lat
