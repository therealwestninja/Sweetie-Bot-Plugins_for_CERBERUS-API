
from sweetiebot.adapters.unitree_go2 import UnitreeGo2Adapter
from sweetiebot.routines.executor import RoutineExecutor
from sweetiebot.cognition.engine import CognitiveEngine
from sweetiebot.audio.queue import SpeechQueue

class SweetieBotRuntime:
    def __init__(self):
        self.adapter = UnitreeGo2Adapter()
        self.adapter.connect()
        self.executor = RoutineExecutor(self.adapter)
        self.cognition = CognitiveEngine()
        self.speech = SpeechQueue()

    def execute_behavior(self, behavior):
        score = self.cognition.score_behavior(behavior)
        if score < 0.2:
            return {"skipped": True}

        routine = behavior.get("routine_id")
        result = self.executor.execute(routine)
        self.cognition.apply_cooldown(routine)
        return result

    def speak(self, text):
        self.speech.add(text)
        return self.adapter.speak(text)
