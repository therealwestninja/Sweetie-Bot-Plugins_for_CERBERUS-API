import { apiGet } from "./api.js";
import { runRoutine } from "./character.js";

export async function loadRoutines() {
  return apiGet("/routines");
}

export async function startRoutine(routineId) {
  return runRoutine(routineId);
}
