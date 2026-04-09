export interface DateRange {
  start: Date | null;
  end: Date | null;
}

export function formatDate(date: Date | null) {
  if (!date) return "";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function parseIsoDate(dateText: string | null): Date | null {
  if (!dateText) return null;
  const [y, m, d] = dateText.split("-").map(Number);
  return new Date(y, m - 1, d);
}
