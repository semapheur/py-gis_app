export interface Point2D {
  x: number;
  y: number;
}

export function round(n: number, decimals: number = 5): number {
  const f = 10 ** decimals;
  return Math.round(n * f) / f;
}

export function fractional(float: number) {
  return float % 1;
}

export function splitFloat(float: number) {
  const integer = Math.trunc(float);
  const decimal = float - integer;
  return { integer, decimal };
}

export function clamp(value: number, min: number, max: number): number {
  return value < min ? min : value > max ? max : value;
}

export function polarToCartesian(deg: number, radius: number, origin: Point2D) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return {
    x: origin.x + radius * Math.cos(rad),
    y: origin.y + radius * Math.sin(rad),
  };
}

export function polarAngle(x: number, y: number) {
  let deg = (Math.atan2(y, x) * 180) / Math.PI + 90;
  return ((deg % 360) + 360) % 360;
}
