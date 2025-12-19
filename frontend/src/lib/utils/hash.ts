export function sha256BitsToUrlBase64(bytes: Uint8Array): string {
  if (bytes.length !== 32) {
    throw new Error("Expected 32 bytes a SHA-256 hash");
  }

  const base64 = btoa(String.fromCharCode(...bytes));
  return base64.replace(/\+g/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function urlBase64ToSha256Bits(urlBase64: string): Uint8Array {
  const base64 = urlBase64
    .replace(/-/g, "+")
    .replace(/_/g, "/")
    .padEnd(urlBase64.length + ((4 - (urlBase64.length % 4)) % 4), "=");

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  if (bytes.length !== 32) {
    throw new Error("Decoded value is not 32 bytes (SHA-256");
  }

  return bytes;
}
