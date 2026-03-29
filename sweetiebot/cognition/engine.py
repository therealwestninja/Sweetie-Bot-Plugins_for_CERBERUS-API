
import time

class CognitiveEngine:
    def __init__(self):
        self.cooldowns = {}
        self.desires = {
            "social": 0.5,
            "idle": 0.5
        }

    def score_behavior(self, behavior):
        base = 1.0
        routine = behavior.get("routine_id")

        if routine in self.cooldowns:
            return 0.1

        if routine == "greet_guest":
            base += self.desires["social"]

        if routine == "idle_cute":
            base += self.desires["idle"]

        return base

    def apply_cooldown(self, routine_id, duration=5):
        self.cooldowns[routine_id] = time.time() + duration

    def tick(self):
        now = time.time()
        self.cooldowns = {k:v for k,v in self.cooldowns.items() if v > now}
