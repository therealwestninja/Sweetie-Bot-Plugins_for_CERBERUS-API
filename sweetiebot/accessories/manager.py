class AccessoryManager:
    def __init__(self) -> None:
        self.state = {
            "face_display": False,
            "tail_servo": False,
            "speaker_stack": True,
        }

    def capabilities(self) -> dict:
        return dict(self.state)
