import { speakInCharacter } from "./character.js";

export function buildDialoguePreview(text, emoteId) {
  return {
    text,
    emoteId,
    preview: `${text} :: ${emoteId ?? "no-emote"}`
  };
}

export async function submitDialogue(text) {
  return speakInCharacter(text);
}
