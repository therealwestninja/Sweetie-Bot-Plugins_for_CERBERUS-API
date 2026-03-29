import { apiGet } from "./api.js";

export function summarizeMemory(memory) {
  return {
    people: memory?.known_people?.length ?? 0,
    preferences: memory?.preferences?.length ?? 0
  };
}

export async function loadMemorySummary() {
  return apiGet("/memory/summary");
}
