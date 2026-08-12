// Thin fetch wrapper -- low-level transport only. Business-shaped calls
// (what path, what params, mock-or-real) belong in each page's endpoints/
// file, not here.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class HttpError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "HttpError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    throw new HttpError(
      response.status,
      `${init?.method ?? "GET"} ${path} failed: ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

export const httpClient = {
  get: <T>(path: string): Promise<T> => request<T>(path),
};
