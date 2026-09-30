const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getStoredAuthToken() {
  return localStorage.getItem("buildsync_token");
}

export function getStoredUser() {
  const raw = localStorage.getItem("buildsync_user");
  return raw ? JSON.parse(raw) : null;
}

export async function apiRequest(path, { method = "GET", body, signal } = {}) {
  const token = getStoredAuthToken();
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    signal,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
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