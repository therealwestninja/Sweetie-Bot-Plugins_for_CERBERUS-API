
class SpeechQueue:
    def __init__(self):
        self.queue = []

    def add(self, text):
        self.queue.append(text)

    def next(self):
        if not self.queue:
            return None
        return self.queue.pop(0)
