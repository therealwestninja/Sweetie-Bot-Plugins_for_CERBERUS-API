from __future__ import annotations

from typing import Any

from sweetiebot.character.intent_types import IntentType
from sweetiebot.dialogue.providers import DialogueProvider


class SweetieBotDialoguePlugin:
    name = 'sweetiebot_dialogue'

    def describe(self) -> dict:
        return {
            'name': self.name,
            'category': 'dialogue',
            'provides': [
                'reply generation',
                'intent tagging',
                'mood triggers',
                'optional llm-backed personality',
                'cerberus audio dispatch hooks',
            ],
        }

    def handle_text(
        self,
        *,
        text: str,
        dialogue_manager,
        persona_machine,
        character,
        llm_provider: DialogueProvider,
        audio_client,
    ) -> dict[str, Any]:
        intent = dialogue_manager.infer_intent(text)
        provider_name = llm_provider.describe().get('provider', 'local')
        if llm_provider.is_configured() and provider_name != 'local':
            provider_reply = llm_provider.generate_reply(
                system_prompt=dialogue_manager.build_system_prompt(),
                user_text=text,
            )
            reply_text = provider_reply.text
            model_name = provider_reply.model
        else:
            local_reply = dialogue_manager.reply_for(text)
            reply_text = local_reply.text
            model_name = llm_provider.describe().get('model', 'rule-based-local')

        emote_id = dialogue_manager.choose_emote(text, reply_text)
        character.is_speaking = True
        trigger_map = {
            IntentType.GREET: 'praised',
            IntentType.SPEAK: 'music' if 'sing' in text.lower() else 'praised',
        }
        character.mood = persona_machine.transition(trigger_map.get(intent, 'praised'))
        audio_result = audio_client.speak(
            text=reply_text,
            metadata={
                'persona_id': character.persona_id,
                'mood': character.mood.value,
                'intent': intent.value,
                'source': provider_name,
                'model': model_name,
            },
        )
        return {
            'heard': text,
            'reply': reply_text,
            'intent': intent.value,
            'emote_id': emote_id,
            'provider': provider_name,
            'model': model_name,
            'audio': {
                'ok': audio_result.ok,
                'sink': audio_result.sink,
                'detail': audio_result.detail,
                'status_code': audio_result.status_code,
            },
            'character': {
                'persona_id': character.persona_id,
                'mood': character.mood.value,
                'attention_target': character.attention_target,
                'active_routine': character.active_routine,
                'is_speaking': character.is_speaking,
            },
        }
