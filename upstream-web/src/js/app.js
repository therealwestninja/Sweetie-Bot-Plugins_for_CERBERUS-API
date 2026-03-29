import { getApiBaseUrl, setApiBaseUrl } from "./api.js";
import { cancelCharacterAction, loadCharacterState, triggerEmote } from "./character.js";
import { loadAccessories } from "./accessories.js";
import { submitDialogue } from "./dialogue.js";
import { connectEventStream } from "./events.js";
import { loadMemorySummary, summarizeMemory } from "./memory.js";
import { applyPersonaPreset, fetchPersonaPresets } from "./persona.js";
import { loadPlugins } from "./plugins.js";
import { loadRoutines, startRoutine } from "./routines.js";

let eventSocket = null;

function $(selector) {
  return document.querySelector(selector);
}

function renderJson(selector, payload) {
  $(selector).textContent = JSON.stringify(payload, null, 2);
}

function appendActivity(entry) {
  const host = $("#activity-log");
  const lines = host.textContent.trim() ? host.textContent.split("\n\n") : [];
  lines.unshift(JSON.stringify(entry, null, 2));
  host.textContent = lines.slice(0, 12).join("\n\n");
}

async function renderPersonaPresets(activePersonaId = null) {
  const host = $("#persona-presets");
  host.innerHTML = "";
  const presets = await fetchPersonaPresets();
  for (const preset of presets) {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${preset.display_name} — ${preset.motion_style?.energy_bias ?? "balanced"}`;
    if (preset.id === activePersonaId) {
      button.disabled = true;
    }
    button.addEventListener("click", async () => {
      const result = await applyPersonaPreset(preset.id);
      appendActivity(result);
      await refreshDashboard();
    });
    li.appendChild(button);
    host.appendChild(li);
  }
}

async function refreshDashboard() {
  const [character, accessories, memory, routines, plugins] = await Promise.all([
    loadCharacterState(),
    loadAccessories(),
    loadMemorySummary(),
    loadRoutines(),
    loadPlugins()
  ]);

  $("#status-line").textContent = `${character.persona_id} · mood=${character.mood} · speaking=${character.is_speaking}`;
  renderJson("#character-state", character);
  renderJson("#accessory-state", accessories);
  renderJson("#memory-state", summarizeMemory(memory));
  renderJson("#plugin-state", plugins);
  await renderPersonaPresets(character.persona_id);

  const routineList = $("#routine-list");
  routineList.innerHTML = "";
  for (const routine of routines.items) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `${routine.id} · ${routine.steps.length} steps`;
    button.title = routine.title;
    button.addEventListener("click", async () => {
      const result = await startRoutine(routine.id);
      appendActivity(result);
      await refreshDashboard();
    });
    routineList.appendChild(button);
  }
}

function handleEvent(event) {
  appendActivity(event);
  if (event.type === "events.snapshot") {
    const snapshot = event.payload;
    renderJson("#character-state", snapshot.character);
    renderJson("#accessory-state", snapshot.accessories);
    renderJson("#memory-state", summarizeMemory(snapshot.memory));
    renderJson("#plugin-state", snapshot.plugins);
    $("#status-line").textContent = `${snapshot.character.persona_id} · mood=${snapshot.character.mood} · speaking=${snapshot.character.is_speaking} · stream=live`;
    void renderPersonaPresets(snapshot.character.persona_id);
    return;
  }

  const character = event.payload?.character;
  if (character) {
    renderJson("#character-state", character);
    $("#status-line").textContent = `${character.persona_id} · mood=${character.mood} · speaking=${character.is_speaking} · stream=live`;
    void renderPersonaPresets(character.persona_id);
  }
}

function connectLiveEvents() {
  if (eventSocket) {
    eventSocket.close();
  }
  eventSocket = connectEventStream({
    onMessage: handleEvent,
    onStatusChange: (status) => {
      const line = $("#status-line");
      if (!line.textContent.includes("stream=")) {
        line.textContent = `${line.textContent} · stream=${status}`;
      } else {
        line.textContent = line.textContent.replace(/stream=[^·]+/, `stream=${status}`);
      }
    }
  });
}

function wireApiSettings() {
  const input = $("#api-base-url");
  input.value = getApiBaseUrl();
  $("#save-api-base-url").addEventListener("click", async () => {
    setApiBaseUrl(input.value);
    connectLiveEvents();
    await refreshDashboard();
  });
}

function wireDialogueForm() {
  $("#dialogue-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = $("#dialogue-input").value.trim();
    if (!text) return;
    const result = await submitDialogue(text);
    appendActivity(result);
    $("#dialogue-input").value = "";
    await refreshDashboard();
  });
}

function wireEmoteActions() {
  $("#emote-curious").addEventListener("click", async () => {
    appendActivity(await triggerEmote("curious_headtilt"));
  });
  $("#emote-happy").addEventListener("click", async () => {
    appendActivity(await triggerEmote("happy_bounce"));
  });
  $("#cancel-action").addEventListener("click", async () => {
    appendActivity(await cancelCharacterAction());
    await refreshDashboard();
  });
}

async function main() {
  wireApiSettings();
  wireDialogueForm();
  wireEmoteActions();
  connectLiveEvents();
  await refreshDashboard();
}

main().catch((error) => {
  $("#status-line").textContent = `Error: ${error.message}`;
  console.error(error);
});
