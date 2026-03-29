import { apiGet } from "./api.js";
import { runRoutine } from "./character.js";

export async function loadRoutineList() {
  const payload = await apiGet("/routines");
  return payload.available;
}

export async function startRoutine(routineId) {
  return runRoutine(routineId);
}
