export interface DateRange {
  start: Date;
  end: Date;
}

export function formatDate(date: Date | null) {
  if (!date) return "";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function formatDatetime(unix: number) {
  return unix ? new Date(unix).toISOString() : undefined;
}

export function parseIsoDate(dateText: string | null): Date | null {
  if (dateText === null) return null;
  const [y, m, d] = dateText.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function startOfDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function parseToUnix(dateText: string) {
  return parseIsoDate(dateText)!.getTime();
}
