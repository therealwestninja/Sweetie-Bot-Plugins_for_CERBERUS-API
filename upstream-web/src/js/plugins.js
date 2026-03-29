import { apiGet } from "./api.js";

export async function loadPlugins() {
  const payload = await apiGet("/plugins");
  return payload.items;
}
