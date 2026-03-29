
import time

class AdvancedRoutineExecutor:
    def __init__(self, adapter):
        self.adapter = adapter

    def run(self, routine):
        results = []
        for step in routine.get("steps", []):
            action = step.get("action")
            delay = step.get("delay", 1)

            if action == "emote":
                results.append(self.adapter.set_emote(step["value"]))
            elif action == "speak":
                results.append(self.adapter.speak(step["value"]))
            elif action == "motion":
                results.append(self.adapter.execute_routine(step["value"]))

            time.sleep(delay)

        return results
