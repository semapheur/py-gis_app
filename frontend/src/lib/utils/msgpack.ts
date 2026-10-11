import { encode, decode } from "@msgpack/msgpack";
import { error } from "@sveltejs/kit";

export interface MsgpackError {
  message?: string;
  status: number;
}

type FetchMsgpackResult<TResponse> =
  { ok: true; data: TResponse } | { ok: false; error: MsgpackError };

export async function fetchMsgpack<TResponse, TBody = unknown>(
  url: string,
  options: {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: TBody;
    headers?: Record<string, string>;
    signal?: AbortSignal;
    fetch?: typeof globalThis.fetch;
  } = {},
): Promise<FetchMsgpackResult<TResponse>> {
  const {
    method = "GET",
    body,
    headers = {},
    signal,
    fetchFn = fetch,
  } = options;

  const encodedBody = body !== undefined ? encode(body) : undefined;

  let response: Response;
  try {
    response = await fetchFn(url, {
      method,
      headers: {
        Accept: "application/msgpack",
        ...(encodedBody ? { "Content-Type": "application/msgpack" } : {}),
        ...headers,
      },
      body: encodedBody,
      signal,
    });
  } catch (error) {
    return {
      ok: false,
      error: {
        message:
          error instanceof DOMException && error.name === "AbortError"
            ? "Request aborted"
            : "Network error",
        status: 0,
      },
    };
  }

  const buffer = await response.arrayBuffer().catch(() => null);

  if (!response.ok) {
    const error = decodeMsgpackError(buffer, response.status);
    return { ok: false, error };
  }

  if (buffer === null) {
    return {
      ok: false,
      error: {
        message: "Failed to read response body",
        status: response.status,
      },
    };
  }

  try {
    const data = decode(new Uint8Array(buffer)) as TResponse;
    return { ok: true, data };
  } catch {
    return {
      ok: false,
      error: { message: "Failed to decode response", status: response.status },
    };
  }
}

function decodeMsgpackError(
  buffer: ArrayBuffer | null,
  status: number,
): MsgpackError {
  if (!buffer || buffer.byteLength === 0) return { status };

  try {
    const decoded = decode(new Uint8Array(buffer)) as {
      detail?: string;
      message?: string;
    };
    if (decoded && typeof decoded === "object")
      return { status, message: decoded.detail ?? decoded.message };
  } catch {}

  return { status };
}

export async function loadMsgpack<TResponse, TBody = unknown>(
  fetch: typeof globalThis.fetch,
  path: string,
  options: {
    query?: Record<string, string>;
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: TBody;
  } = {},
): Promise<TResponse> {
  const { query, ...rest } = options;
  const url = query ? `${path}?${new URLSearchParams(query)}` : path;

  const result = await fetchMsgpack<TResponse, TBody>(url, { ...rest, fetch });
  if (!result.ok) {
    const { status, message } = result.error;
    error(
      status >= 400 && status < 600 ? status : 503,
      message ?? "Request failed",
    );
  }
  return result.data;
}
