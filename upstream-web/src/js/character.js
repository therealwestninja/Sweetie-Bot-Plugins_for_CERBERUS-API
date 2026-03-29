import { apiGet, apiPost } from "./api.js";

export async function loadCharacterState() {
  return apiGet("/character");
}

export async function triggerEmote(emoteId = null) {
  return apiPost("/character/emote", { emote_id: emoteId });
}

export async function speakInCharacter(text) {
  return apiPost("/character/say", { text });
}

export async function runRoutine(routineId) {
  return apiPost("/character/routine", { routine_id: routineId });
}

export async function cancelCharacterAction() {
  return apiPost("/character/cancel");
}
