/**
 * nudge.js — Companion Web Interface nudge layer
 *
 * Instead of directly commanding Sweetie-Bot, the operator sends nudges.
 * Sweetie-Bot reacts with a micro-reaction, then decides what to do.
 *
 * Nudge types:
 *   attention   → "Hello?" — get her attention
 *   interaction → "Oh, hi!" — friendly wave
 *   interrupt   → "Hey, quit it!" — stop current action
 *   physical    → "Oof~!" — poke / jostle
 *   encourage   → praise / approval
 *   calm        → settle down, return to neutral
 */

import { apiPost, apiGet } from "./api.js";

/**
 * Send a nudge to Sweetie-Bot.
 * Returns the NudgeResult with micro_reaction and autonomy_decision.
 */
export async function sendNudge(nudgeType, source = "companion_web") {
  return apiPost("/character/nudge", { nudge_type: nudgeType, source });
}

export async function getNudgeStatus() {
  return apiGet("/character/nudge/status");
}

/**
 * Render a nudge result into the activity log.
 * Shows what she said and what she decided to do.
 */
export function formatNudgeResult(result) {
  const { nudge_type, micro_reaction, autonomy_decision, suggested_action, suppressed } = result;
  const lines = [
    `[nudge: ${nudge_type}]`,
    `  "${micro_reaction.speech}"  (${micro_reaction.emote})`,
    `  decision: ${autonomy_decision}`,
  ];
  if (suggested_action) lines.push(`  → will: ${suggested_action}`);
  if (suppressed) lines.push(`  ⚠ spam suppressed`);
  return lines.join("\n");
}
