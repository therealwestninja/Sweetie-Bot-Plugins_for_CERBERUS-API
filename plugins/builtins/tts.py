
class SimpleTTSPlugin:
    plugin_id = "sweetiebot.tts.simple"

    def speak(self, text: str):
        return {
            "text": text,
            "audio": None,
            "status": "tts_stub"
        }
