
from typing import Optional


class CerberusAdapterBase:
    adapter_id = "base.adapter"

    def connect(self):
        raise NotImplementedError

    def execute_routine(self, routine_id: str):
        raise NotImplementedError

    def set_emote(self, emote_id: str):
        raise NotImplementedError

    def speak(self, text: str):
        raise NotImplementedError
