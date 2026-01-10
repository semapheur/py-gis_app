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
