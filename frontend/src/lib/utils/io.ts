export function exportFile(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();

  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function parseCsv(text: string): Record<string, string | number>[] {
  const lines = text.split("\n").filter((line) => line.trim());
  if (lines.length === 0) return [];

  const headers = lines[0]
    .split(",")
    .map((h) => h.trim().replace(/^"|"$/g, ""));
  const rows: Record<string, string | number>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const values: string[] = [];
    let current = "";
    let insideQuotes = false;

    for (let char of lines[i]) {
      if (char === '"') {
        insideQuotes = !insideQuotes;
      } else if (char === "," && !insideQuotes) {
        values.push(current.trim().replace(/^"|"$/g, ""));
        current = "";
      } else {
        current += char;
      }
    }
    values.push(current.trim().replace(/^"|"$/g, ""));

    const row: Record<string, string | number> = {};
    headers.forEach((header, index) => {
      const value = values[index] || "";
      const numValue = Number(value);
      row[header] = !isNaN(numValue) && value !== "" ? numValue : value;
    });

    if (!row.id) {
      row.id = `row_${Date.now()}_${i}`;
    }

    rows.push(row);
  }

  return rows;
}

export function parseJson(text: string): Record<string, string | number>[] {
  try {
    const parsed = JSON.parse(text);
    const rows = Array.isArray(parsed) ? parsed : [parsed];

    return rows.map((row, index) => {
      if (!row.id) {
        row.id = `row_${Date.now()}_${index}`;
      }
      return row;
    });
  } catch (error) {
    console.error("Failed to parse JSON:", error);
    throw new Error("Invalid JSON format");
  }
}
