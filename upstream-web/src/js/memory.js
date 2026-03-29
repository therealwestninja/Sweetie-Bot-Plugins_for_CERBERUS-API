export function summarizeMemory(memory) {
  return {
    people: memory?.known_people?.length ?? 0,
    preferences: memory?.preferences?.length ?? 0
  };
}
