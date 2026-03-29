
from fastapi import FastAPI
from pydantic import BaseModel

from sweetiebot.runtime import SweetieBotRuntime

app = FastAPI()
runtime = SweetieBotRuntime()

class SpeakRequest(BaseModel):
    text: str

@app.post("/speak")
def speak(payload: SpeakRequest):
    return runtime.speak(payload.text)
