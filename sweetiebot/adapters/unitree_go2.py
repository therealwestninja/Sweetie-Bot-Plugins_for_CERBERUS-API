
from sweetiebot.adapters.base import CerberusAdapterBase


class UnitreeGo2Adapter(CerberusAdapterBase):
    adapter_id = "unitree.go2.adapter"

    def __init__(self):
        self.connected = False

    def connect(self):
        # placeholder for real SDK connection
        self.connected = True
        return {"connected": True}

    def execute_routine(self, routine_id: str):
        mapping = {
            "greet_guest": "shake_hand",
            "photo_pose": "stand_pose",
            "idle_cute": "wag_tail",
        }
        motion = mapping.get(routine_id, "stand_pose")
        return {
            "routine": routine_id,
            "mapped_motion": motion,
            "status": "executed_stub"
        }

    def set_emote(self, emote_id: str):
        return {
            "emote": emote_id,
            "status": "applied_stub"
        }

    def speak(self, text: str):
        return {
            "spoken": text,
            "status": "tts_stub"
        }
