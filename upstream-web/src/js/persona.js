import { loadPersonaList, switchPersona } from "./character.js";

export async function fetchPersonaPresets() {
  return loadPersonaList();
}

export async function applyPersonaPreset(personaId) {
  return switchPersona(personaId);
}
