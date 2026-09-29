const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiRequest(path, { method = "GET", body, signal } = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    signal,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return null;

  const responseText = await response.text();
  let result;
  try {
    result = responseText ? JSON.parse(responseText) : null;
  } catch {
    result = responseText;
  }

  if (!response.ok) {
    const message =
      typeof result === "string" ? result : result?.detail || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return result;
}