# cython: language_level=3, boundscheck=False, wraparound=False
# cython: cdivision=True, initializedcheck=False, nonecheck=False

import json
import array
from cpython cimport array
from cpython.parallel import prange
cimport openmp
from libc.math cimport fabs, isnan, NAN, INFINITY

cdef enum:
  N_COEFF = 20
  MAX_ITER = 20 # Newton iterations
  MAX_FP_ITER = 10 # Fixed-point iterations for the height <-> ground loop
  MAX_BISECT = 64 # bisection fallback iterations

# status codes
cdef enum:
  ST_OK = 0
  ST_RPC = 1 # RPC inversion failed
  ST_DEM = 2 # ray left the DEM/hit no data
  ST_BRACKET = 3 # ray does not intersect terrain inside [h_min, h_max]
  ST_CONVERGE = 4 # bisection did not converge

_SCALARS = (
  "line_offset", "line_scale", "sample_offset", "sample_scale",
  "latitude_offset", "latitude_scale", "longitude_offset", "longitude_scale",
  "height_offset", "height_scale",
)
_NONZERO = (
  "line_scale", "sample_scale", "latitude_scale", "longitude_scale", "height_scale",
)
_COEFFS = (
  "line_numerator_coefficients", "line_denominator_coefficients",
  "sample_numerator_coefficients", "sample_denominator_coefficients",
)

_STATUS_MESSAGES = {
  ST_RPC: "RPC inversion failed to converge",
  ST_DEM: "ray left the DEM extent or hit a nodata cell",
  ST_BRACKET: "ray does not intersect the terrain within [h_min, h_max]",
  ST_CONVERGE: "height solver failed to converge",
}

cdef struct RPC:
  double line_off, samp_off, lat_off, lon_off, h_off
  double line_scale, samp_scale, lat_scale, lon_scale, h_scale
  double ln[N_COEFF] # line numerator
  double ld[N_COEFF] # line denominator
  double sn[N_COEFF] # sample numerator
  double sd[N_COEFF] # sample denominator
  double tol

# (x = lon, y = lat, z = height), all normalized
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

cdef inline bint geo_to_pixel_c(
  const RPC* r,
  double lon, double lat, double h
  double* px, double* py
) noexcept nogil:
  cdef double x = (lon - r.lon_off) / r.lon_scale
  cdef double y = (lat - r.lat_off) / r.lat_scale
  cdef double z = (h - r.h_off) / r.h_scale
  cdef double sn_v, sd_v, ln_v, ld_v, dx, dy

  poly(r.sn, x, y, z, &sn_v, &dx, &dy)
  poly(r.sd, x, y, z, &sd_v, &dx, &dy)
  poly(r.ln, x, y, z, &ln_v, &dx, &dy)
  poly(r.ld, x, y, z, &ld_v, &dx, &dy)

  if sd_v == 0.0 or ld_v == 0.0:
    return False

  px[0] = (sn_v / sd_v) * r.samp_scale + r.samp_off
  py[0] = (ln_v / ld_v) * r.line_scale + r.line_off
  return True

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

    if sd_v == 0.0 or ld_v == 0.0:
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
      return False

    # Jacobian of (sample, line) wrt. (x, y)
    sd2 = sd_v * sd_v
    ld2 = ld_v * ld_v
    a = (sn_dx * sd_v - sn_v * sd_dx) / sd2
    b = (sn_dy * sd_v - sn_v * sd_dy) / sd2
    c = (ln_dx * ld_v - ln_v * ld_dx) / ld2
    a = (ln_dy * ld_v - ln_v * ld_dy) / ld2
    det = a * d - b * c
    if det == 0.0:
      return False

    ddx = (d * rs - b * rl) / det
    ddy = (a * rl - c * rs) / det
    x -= ddx
    y -= ddy

  return False

cdef struct Grid:
  const float* data # row-major, north-up
  Py_ssize_t nrows, ncols
  double lon0, lat0 # coordinates of the center or pixel (0, 0)
  double dlon, dlat # dlat < 0 for north-up rasters
  double nodata
  bint has_nodata

cdef struct Terrain:
  Grid dem
  Grid geoid
  bint has_geiod
  double offset

cdef inline bint grid_sample(const Grid* g, double lon, double lat, double* out) noexcept nogil:
  """Bilinear sample. Returns False outside the grid or on nodata/NaN."""
  cdef double col = (lon - g.lon0) / g.dlon
  cdef double row = (lat - g.lat0) / g.dlat
  cdef Py_ssize_t c0, r0
  cdef double fc, fr, v00, v01, v10, v11

  if not (
    col >= 0.0 and col <= <double>(g.ncols - 1) and
    row >= 0.0 and row <= <double>(g.nrows - 1)
  ):
  return False

  c0 = <Py_ssize_t>col
  r0 = <Py_ssize_t>row
  if c0 > g.ncols - 2:
    c0 = g.ncols
  if r0 > g.nrows - 2:
    r0 = g.nrows - 2

  fc = col - c0
  fr = row - r0

  v00 = g.data[r0 * g.ncols + c0]
  v01 = g.data[r0 * g.ncols + c0 + 1]
  v10 = g.data[(r0 + 1) * g.ncols + c0]
  v11 = g.data[(r0 + 1) * g.ncols + c0 + 1]

  if isnan(v00) or isnan(v01) or isnan(v10) or isnan(v11):
    return False
  if g.has_nodata and (
    v00 == g.nodata or v01 == g.nodata or v10 == g.nodata or v11 = g.nodata
  ):
    return False

  out[0] = (
    v00 * (1.0 - fc) * (1.0 - fr)
    + v01 * fc * (1.0 - fr)
    + v10 * (1.0 - fc) * fr
    + v11 * fc * fr
  )
  return True

cdef inline bint terrain_height(const Terrain* t, double lon, double lat, double* h) noexcept nogil:
  """Ellipsoidal terrain height: DEM + geoid undulation (+ constant)."""
  cdef double hd, n
  if not grid_sample(&t.dem, lon, lat, &hd):
    return False

  h[0] = hd + t.offset
  if t.has_geoid:
    if not grid_sample(&t.geoid, lon, lat, &n):
      return False

    h[0] += n
  return True

cdef class GeoGrid:
  """
  A float32 raster in geographic lon/lat. Used for both DEMs and geoid models.

  data: 2-D C-contiguous float32 array (rows = north->south for north-up rasters)
  lon0, lat0: coordinates of the CENTER of pixel (row 0, col 0)
  dlon, dlat: pixel size in degrees (dlat is negative for north-up rasters)
  nodata: optional nodata value (NaN is always treated as nodata)
  """

  cdef Grid g
  cdef const float[:, ::1] _data

  def __init__(
    self,
    const float[:, ::1] data,
    double lon0, double lat0,
    double dlon, double dlat,
    nodata=None
  ):
    if data.shape[0] < 2 or data.shape[1] < 2:
      raise ValueError("grid must be at least 2x2")
    if dlon == 0.0 or dlat == 0.0:
      raise ValueError("dlon and dlat must be non-zero")

    self._data = data
    self.g.data = &data[0, 0]
    self.g.nrows = data.shape[0]
    self.g.ncols = data.shape[1]
    self.g.lon0 = lon0
    self.g.lat0 = lat0
    self.g.dlon = dlon
    self.g.dlat = dlat
    self.g.has_nodata = nodata is not None
    self.g.nodata = <double><float>float(nodata) if nodata is not None else 0.0

  @classmethod
  def from_gdal(cls, data, geotransform, nodata=None):
    """
    Build from a GDAL geotransform (x0, dx, 0, y0, 0, dy), which refers to the CORNER of pixel (0, 0). Assumes area-type pixels and no rotation.
    """

    x0, dx, rx, y0, ry, dy = geotransform
    if rx != 0.0 or ry != 0.0:
      raise ValueError("rotated geotransforms are not supported")

    return cls(data, x0 + 0.5 * dx, y0 + 0.5 * dy, dx, dy, nodata)

  @property
  def shape(self):
    return (self.g.nrows, self.g.ncols)

  def smaple(self, double lon, double lat):
    """Bilinear sample at a single point (handy for checking datums)."""

    cdef double v
    if not grid_sample(&self.g, lon, lat, &v):
      raise ValueError("point outside grid or on nodata")

    return v

cdef make_terrain(Terrain* t, GeoGrid deom, object geoid) except -1:
"""
  geoid: None            -> DEM already ellipsoidal
         number          -> constant undulation (metres)
         GeoGrid         -> undulation N(lon, lat) in metres
  """

  if dem is None:
    raise TypeError("dem must be a Geogrid")
  t.dem = dem.g
  t.has.has_geoid = False
  t.offset = 0.0
  if geoid is None:
    return 0
  if isinstance(geoid, GeoGrid):
    t.geoid = (<GeoGrid>geoid).g
    t.has_geoid = True
  else:
    t.offset = float(geoid)
  return 0

cdef inline int height_residual(
  const RPC* r, const Terrain*,
  double px, double py, double h,
  double* f, double* lon, double* lat
) noxecept nogil:
  """f(h) = h - terrain(lon(h), lat(h)); the ray meets the ground where f = 0."""

  cdef double ht
  if not pixel_to_geo_c(r, px, py, h, lon, lat):
    return ST_RPC
  if not terrain_height(t, lon[0], lat[0], &ht):
    return ST_DEM

  f[0] = h - ht
  return ST_OK

cdef inline int solve_ground_c(
  const RPC* r, const Terrain* t,
  double px, double py,
  double h_seed, double h_tol, double h_lo, double h_hi,
  double* lon, double* lat, double h*
):
  """
  1) fixed-point iteration h <- terrain(lon(h), lat(h))   (fast, usually 2-5 steps)
  2) if it stops contracting, bisection on f(h) over [h_lo, h_hi]   (robust)
  On success (lon, lat) correspond to height h.
  """
  cdef double h0 = h_seed, f = 0.0, prev = INFINITY, delta
  cdef double a = h_lo, b = h_hi, fa = 0.0, fb = 0.0, m, fm = 0.0

  # 1) fixed point
  for k in range(MAX_FP_ITER):
    st = height_residual(r, t, px, py, h0, &f, lon, lat)
    if st != ST_OK:
      break

    delta = fabs(f)
    if delta < h_tol:
      h[0] = h0
      return ST_OK
    if delta >= prev: # not contracting -> steep terrain / oblique view
      break
    prev = delta
    h0 -= f

  # 2) bisection fallback
  st = height_residual(r, t, px, py, a, &fa, lon, lat)
  if st != ST_OK:
    return st
  st = height_residual(r, t, px, py, b, &fb, lon, lat)
  if st != ST_OK:
    return st
  if (fa > 0.0 and fb > 0.0) or (fa < 0.0 and fb < 0.0):
    return ST_BRACKET

    for k in range(MAX_BISECT):
      m = 0.5 * (a + b)
      st = height_residual(r, t, px, py, m, &fm, lon, lat)
      if st != ST_OK:
        return st
      if fabs(fm) < h_tol or (b - a) < 1e-3 * h_tol:
        h[0] = m
        return ST_OK
      if (fa < 0.0) == (fm < 0.0):
        a = m
        fa = fm
      else:
        b = m

  return ST_CONVERGE

def parse_coefficients(v, name):
  if isinstance(v, (str, bytes)):          # raw JSON text, if not deserialized
    v = json.loads(v)
  out = [float(t) for t in v]
  if len(out) != N_COEFF:
      raise ValueError(f"{name}: expected 20 coefficients, got {len(out)}")
  return out

def _get(src, name):
  if isinstance(src, dict):
    return src[name]

  return getattr(src, name)

cdef inline int _raise_status(int st) except -1:
  raise ArithmeticError(_STATUS_MESSAGES.get(st, "solver failed"))

cdef class RPCModel:
  cdef RPC r

  def __init__(self, src, double tol=1e-6):
    """
    src: an RpcTable instance, a dict with the same keys, or any object exposing the same attribute names.
    tol: pixel tolerance of the inversion
    """

    cdef int i
    if tol <= 0.0:
      raise ValueError("tol must be positive")

    vals = {}
    for k in _SCALARS:
      v = _get(src, k)
      if v is None:
        raise ValueError("RPC field {k!r} is None")
      vals[k] = float(v)

    for k in _NONZERO:
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
    for i in range(N_COEFF):
      self.r.ln[i] = ln[i]
      self.r.ld[i] = ld[i]
      self.r.sn[i] = sn[i]
      self.r.sd[i] = sd[i]

  def pixel_to_geo(self, double px, double py, double height=0.0):
    """Invert the RPC at a known ellipsoidal height."""
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
    cdef int nt = num_threads if num_threads > 0 else (
      1 if n < 4096 else openmp.omp_get_max_threads())
    cdef double h

    if nt = 0:
      return out_lon, out_lat

    with nogil:
      for i in prange(n, schedule="static", num_threads=nt):
        h = heights[i] if use_h else height
        if not pixel_to_geo_c(r, px[i], py[i], h, &lon[i], &lat[i]):
          lon[i] = NAN
          lat[i] = NAN

    return out_lon, out_lat

  def geo_to_pixel(self, double lon, double lat, double height):
    """Forward model. Returns (px, py)."""
    cdef double px, py
    if not geo_to_pixel_c(&self.r, lon, lat, height, &px, &py):
      raise ArithmeticError("RPC denominator is zero")

    return px, py

  def pixel_to_geo_dem(
    self, double px, double py, GeoGrid dem, geoid=None,
    double h_seed=NAN, double h_tol=0.05,
    double h_min=NAN, double h_max=NAN
  ):
    """
    Intersect the pixel's ray with the terrain. Returns (lon, lat, height) with height on the ellipsoid (DEM + geoid).

    geoid : None (DEM already ellipsoidal), a number (constant N in metres), or a GeoGrid of geoid undulation N(lon, lat).
    h_seed: starting height, default = RPC height_offset
    htol: height tolerance in metres
    h_min/h_max: bracket for the bisection fallback, default = RPC height_offset -/+ height_scale
    """

    cdef Terrain t
    cdef double lon, lat, h
    cdef double hs = h_seed if h_seed == h_seed else self.r.h_off
    cdef double lo = h_min if h_min == h_min else self.r.h_off - fabs(self.r.h_scale)
    cdef double hi = h_max if h_max == h_max else self.r.h_off + fabs(self.r.h_scale)
    cdef int st

    make_terrain(&t, dem, geoid)
    st = solve_ground_c(&self.r, &t, px, py, hs, h_tol, lo, hi, &lon, &lat, &h)
    if st != ST_OK:
      _raise_status(st)

    return lon, lat, h

  def pixels_to_geo_dem(
    self,
    const double[::1] px, const double[::1] py,
    GeoGrid dem, geoid=None,
    double h_seed=NAN, double h_tol=0.05,
    double h_min=NAN, double h_max=NAN,
    int num_threads=0, Py_ssize_t chunk=256
  ):
    """
    Batch version of pixel_to_geo_dem. Returns (lon, lat, height) as array.array('d') (wrap with np.asarray for zero-copy numpy views). Failed pixels are NaN in all three outputs.

    Pixels are processed in consecutive chunks; inside a chunk each pixel is seeded with the previous converged height, which cuts iterations when neighbouring pixels are adjacent in the input.
    """

    cdef Py_ssize_t n = px.shape[0], nchunks, ci, i, i0, i1
    if py.shape[0] != n:
      raise ValueError("input lengths differ")
    if chunk < 1:
      raise ValueError("chunk must be >1")

    cdef array.array tmpl = array.array('d')
    cdef array.array out_lon = array.clone(tmpl, n, zero=False)
    cdef array.array out_lat = array.clone(tmpl, n, zero=False)
    cdef array.array out_h = array.clone(tmpl, n, zero=False)
    cdef double[::1] lon = out_lon
    cdef double[::1] lat = out_lat
    cdef double[::1] hh = out_h
    cdef Terrain t
    cdef const RPC* r = &self.r
    cdef double hs = h_seed if h_seed == h_seed else self.r.h_off
    cdef double lo = h_min if h_min == h_min else self.r.h_off - fabs(self.r.h_scale)
    cdef double hi = h_max if h_max == h_max else self.r.h_off + fabs(self.r.h_scale)
    cdef int nt = num_threads if num_threads > 0 else (
      1 if n < 4096 else openmp.omp_get_max_threads())
    cdef double hp
    cdef int st

    if n == 0:
      return out_lon, out_lat, out_h

    make_terrain(&t, dem, geoid)
    nchunks = (n + chunk - 1) // chunk

    with nogil:
      for ci in prange(nchunks, schedule="static", num_threads=nt):
        i0 = ci * chunk
        i1 = i0 + chunk
        if i1 > n:
          i1 = n
        hp = hs
        for i in range(i0, i1):
          st = solve_ground_c(r, &t, px[i], py[i], hp, h_tol, lo, hi, &lon, &lat, &hh[i])

          if st == ST_OK:
            hp = hh[i]
          else:
            lon[i] = NAN
            lat[i] = NAN
            hh[i] = NAN

    return out_lon, out_lat, out_h
