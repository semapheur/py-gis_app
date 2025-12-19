export function round(n: number, decimals: number = 5): number {
  const f = 10 ** decimals;
  return Math.round(n * f) / f;
}
