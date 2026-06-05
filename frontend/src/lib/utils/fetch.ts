import { encode, decode } from "@msgpack/msgpack";

export interface MsgpackError {
  message?: string;
  status: number;
}

type FetchMsgpackResult<TResponse> =
  | { ok: true; data: TResponse }
  | { ok: false; error: MsgpackError };

export async function fetchMsgpack<TResponse, TBody = unknown>(
  url: string,
  options: {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: TBody;
    headers?: Record<string, string>;
    signal?: AbortSignal;
  } = {},
): Promise<FetchMsgpackResult<TResponse>> {
  const { method = "GET", body, headers = {}, signal } = options;

  const encodedBody = body !== undefined ? encode(body) : undefined;

  let response: Response;
  try {
    response = await fetch(url, {
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

  const decoded = decode(new Uint8Array(buffer)) as MsgpackError;
  if (decoded && typeof decoded === "object") return { ...decoded, status };

  return { status };
}
