export interface RpcParams {
  line_offset: number;
  line_scale: number;
  sample_offset: number;
  sample_scale: number;
  latitude_offset: number;
  latitude_scale: number;
  longitude_offset: number;
  longitude_scale: number;
  height_offset: number;
  height_scale: number;
  line_numerator_coefficients: number[];
  line_denominator_coefficients: number[];
  sample_numerator_coefficients: number[];
  sample_denominator_coefficients: number[];
}

interface PolyResult {
  v: number;
  dx: number;
  dy: number;
  dz: number;
}

export function polyAndGrad(
  c: readonly number[],
  x: number,
  y: number,
  z: number,
): PolyResult {
  const xx = x * x,
    yy = y * y,
    zz = z * z;
  const xy = x * y,
    xz = x * z,
    yz = y * z;

  const v =
    c[0] +
    c[1] * x +
    c[2] * y +
    c[3] * z +
    c[4] * xy +
    c[5] * xz +
    c[6] * yz +
    c[7] * xx +
    c[8] * yy +
    c[9] * zz +
    c[10] * xy * z +
    c[11] * xx * x +
    c[12] * x * yy +
    c[13] * x * zz +
    c[14] * xx * y +
    c[15] * yy * y +
    c[16] * y * zz +
    c[17] * xx * z +
    c[18] * yy * z +
    c[19] * zz * z;

  const dx =
    c[1] +
    c[4] * y +
    c[5] * z +
    2.0 * c[7] * x +
    c[10] * yz +
    3.0 * c[11] * xx +
    c[12] * yy +
    c[13] * zz +
    2.0 * c[14] * xy +
    2.0 * c[17] * xz;

  const dy =
    c[2] +
    c[4] * x +
    c[6] * z +
    2.0 * c[8] * y +
    c[10] * xz +
    2.0 * c[12] * xy +
    c[14] * xx +
    3.0 * c[15] * yy +
    c[16] * zz +
    2.0 * c[18] * yz;

  const dz =
    c[3] + // ∂(c3 z)/∂z
    c[5] * x + // ∂(c5 xz)/∂z
    c[6] * y + // ∂(c6 yz)/∂z
    2.0 * c[9] * z + // ∂(c9 z^2)/∂z
    c[10] * xy + // ∂(c10 xyz)/∂z
    c[13] * x * 2.0 * z + // ∂(c13 x z^2)/∂z
    c[16] * y * 2.0 * z + // ∂(c16 y z^2)/∂z
    c[17] * xx + // ∂(c17 x^2 z)/∂z
    c[18] * yy + // ∂(c18 y^2 z)/∂z
    3.0 * c[19] * zz; // ∂(c19 z^3)/∂z

  return { v, dx, dy, dz };
}

export class RpcModel {
  #params: RpcParams;
  #height: number;
  #tolerance: number;

  constuctor(params: RpcParams, height?: number, tolerance: number = 1e-6) {
    this.#params = params;
    this.#height = height !== undefined ? height : params.height_offset;
    this.#tolerance = tolerance;
  }

  groundToImage(lon: number, lat: number, height?: number): [number, number] {
    const p = this.#params;
    const h = height !== undefined ? height : this.#height;

    const x = (lon - p.longitude_offset) / p.longitude_scale;
    const y = (lat - p.latitude_offset) / p.latitude_scale;
    const z = (h - p.height_offset) / p.height_scale;

    const s =
      polyAndGrad(p.sample_numerator_coefficients, x, y, z).v /
      polyAndGrad(p.sample_denominator_coefficients, x, y, z).v;

    const l =
      polyAndGrad(p.line_numerator_coefficients, x, y, z).v /
      polyAndGrad(p.line_denominator_coefficients, x, y, z).v;

    return [
      s * p.sample_scale + p.sample_offset,
      l * p.line_scale + p.line_offset,
    ];
  }

  #groundToImageWithJacobian(lon: number, lat: number, height?: number) {
    const p = this.#params;
    const h = height !== undefined ? height : this.#height;

    const x = (lon - p.longitude_offset) / p.longitude_scale;
    const y = (lat - p.latitude_offset) / p.latitude_scale;
    const z = (h - p.height_offset) / p.height_scale;

    const Sn = polyAndGrad(p.sample_numerator_coefficients, x, y, z);
    const Sd = polyAndGrad(p.sample_denominator_coefficients, x, y, z);
    const Ln = polyAndGrad(p.line_numerator_coefficients, x, y, z);
    const Ld = polyAndGrad(p.line_denominator_coefficients, x, y, z);

    const sNorm = Sn.v / Sd.v;
    const lNorm = Ln.v / Ld.v;

    const dSdx = (Sn.dx * Sd.v - Sn.v * Sd.dx) / (Sd.v * Sd.v);
    const dSdy = (Sn.dy * Sd.v - Sn.v * Sd.dy) / (Sd.v * Sd.v);
    const dSdz = (Sn.dz * Sd.v - Sn.v * Sd.dz) / (Sd.v * Sd.v);

    const dLdx = (Ln.dx * Ld.v - Ln.v * Ld.dx) / (Ld.v * Ld.v);
    const dLdy = (Ln.dy * Ld.v - Ln.v * Ld.dy) / (Ld.v * Ld.v);
    const dLdz = (Ln.dz * Ld.v - Ln.v * Ld.dz) / (Ld.v * Ld.v);

    const dLon = 1.0 / p.longitude_scale;
    const dLat = 1.0 / p.latitude_scale;
    const dH = 1.0 / p.height_scale;

    const dS_dLon = dSdx * dLon;
    const dS_dLat = dSdy * dLat;
    const dS_dH = dSdz * dH;

    const dL_dLon = dLdx * dLon;
    const dL_dLat = dLdy * dLat;
    const dL_dH = dLdz * dH;

    const s = sNorm * p.sample_scale + p.sample_offset;
    const l = lNorm * p.line_scale + p.line_offset;

    return { s, l, dS_dLon, dS_dLat, dS_dH, dL_dLon, dL_dLat, dL_dH };
  }

  imageToGround(
    sample: number,
    line: number,
    height?: number,
  ): [number, number] {
    const p = this.#params;
    const h = height !== undefined ? height : this.#height;

    let lon = p.longitude_offset;
    let lat = p.latitude_offset;

    for (let i = 0; i < 20; i++) {
      const {
        s,
        l,
        dS_dLon: a,
        dS_dLat: b,
        dL_dLon: c,
        dL_dLat: d,
      } = this.#groundToImageWithJacobian(lon, lat, h);

      const rs = s - sample;
      const rl = l - line;

      if (Math.abs(rs) < this.#tolerance && Math.abs(rl) < this.#tolerance) {
        return [lon, lat];
      }

      const det = a * d - b * c;
      if (!isFinite(det) || det === 0) break;

      lon -= (d * rs - b * rl) / det;
      lat -= (a * rl - c * rs) / det;
    }

    throw new Error("RPC inversion failed to converge");
  }
}
