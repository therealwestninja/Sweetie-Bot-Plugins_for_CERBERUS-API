
import time
from typing import Optional


class SweetieBotLoop:
    def __init__(self, runtime, tick_rate: float = 1.0):
        self.runtime = runtime
        self.tick_rate = tick_rate
        self.running = False

    def start(self):
        self.running = True
        while self.running:
            self.tick()
            time.sleep(self.tick_rate)

    def stop(self):
        self.running = False

    def tick(self):
        # perception
        self.runtime.apply_perception()

        # attention
        self.runtime.apply_attention()

        # behavior
        result = self.runtime.suggest_and_arbitrate_behavior()

        # execution
        behavior = result.get("behavior", {})
        self.runtime.execute_behavior(behavior)
