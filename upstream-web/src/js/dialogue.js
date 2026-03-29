export function buildDialoguePreview(text, emoteId) {
  return {
    text,
    emoteId,
    preview: `${text} :: ${emoteId ?? "no-emote"}`
  };
}
