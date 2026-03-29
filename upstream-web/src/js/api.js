const DEFAULT_BASE_URL = "http://127.0.0.1:8080";

export function getApiBaseUrl() {
  const configured = window.localStorage.getItem("sweetiebot.apiBaseUrl");
  return configured || DEFAULT_BASE_URL;
}

export function setApiBaseUrl(baseUrl) {
  window.localStorage.setItem("sweetiebot.apiBaseUrl", baseUrl.trim());
}

export async function apiGet(path) {
  const response = await fetch(`${getApiBaseUrl()}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return response.json();
}

export async function apiPost(path, payload = {}) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with ${response.status}`);
  }
  return response.json();
}
