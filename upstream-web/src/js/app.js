import { getApiBaseUrl, setApiBaseUrl } from "./api.js";
import { cancelCharacterAction, loadCharacterState, submitDialogue, triggerEmote } from "./character.js";
import { loadAccessories } from "./accessories.js";
import { loadMemorySummary, summarizeMemory } from "./memory.js";
import { personaPresets } from "./persona.js";
import { loadRoutineList, startRoutine } from "./routines.js";

function $(selector) {
  return document.querySelector(selector);
}

function renderJson(selector, payload) {
  $(selector).textContent = JSON.stringify(payload, null, 2);
}

function renderPersonaPresets() {
  const host = $("#persona-presets");
  host.innerHTML = "";
  for (const preset of personaPresets) {
    const li = document.createElement("li");
    li.textContent = `${preset.label} — ${preset.flavor}`;
    host.appendChild(li);
  }
}

async function refreshDashboard() {
  const [character, accessories, memory, routines] = await Promise.all([
    loadCharacterState(),
    loadAccessories(),
    loadMemorySummary(),
    loadRoutineList()
  ]);

  $("#status-line").textContent = `${character.persona_id} · mood=${character.mood} · speaking=${character.is_speaking}`;
  renderJson("#character-state", character);
  renderJson("#accessory-state", accessories);
  renderJson("#memory-state", summarizeMemory(memory));

  const routineList = $("#routine-list");
  routineList.innerHTML = "";
  for (const routineId of routines) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = routineId;
    button.addEventListener("click", async () => {
      const result = await startRoutine(routineId);
      renderJson("#activity-log", result);
      await refreshDashboard();
    });
    routineList.appendChild(button);
  }
}

function wireApiSettings() {
  const input = $("#api-base-url");
  input.value = getApiBaseUrl();
  $("#save-api-base-url").addEventListener("click", async () => {
    setApiBaseUrl(input.value);
    await refreshDashboard();
  });
}

function wireDialogueForm() {
  $("#dialogue-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = $("#dialogue-input").value.trim();
    if (!text) return;
    const result = await submitDialogue(text);
    renderJson("#activity-log", result);
    $("#dialogue-input").value = "";
    await refreshDashboard();
  });
}

function wireEmoteActions() {
  $("#emote-curious").addEventListener("click", async () => {
    renderJson("#activity-log", await triggerEmote("curious_headtilt"));
  });
  $("#emote-happy").addEventListener("click", async () => {
    renderJson("#activity-log", await triggerEmote("happy_bounce"));
  });
  $("#cancel-action").addEventListener("click", async () => {
    renderJson("#activity-log", await cancelCharacterAction());
    await refreshDashboard();
  });
}

async function main() {
  renderPersonaPresets();
  wireApiSettings();
  wireDialogueForm();
  wireEmoteActions();
  await refreshDashboard();
}

main().catch((error) => {
  $("#status-line").textContent = `Error: ${error.message}`;
  console.error(error);
});
