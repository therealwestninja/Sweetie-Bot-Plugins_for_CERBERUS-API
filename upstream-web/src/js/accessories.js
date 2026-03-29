import { apiGet } from "./api.js";

export async function loadAccessories() {
  return apiGet("/accessories");
}
