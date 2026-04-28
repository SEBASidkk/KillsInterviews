import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # === AUDIO ===
    SAMPLE_RATE: int = 16000
    CHUNK_DURATION_MS: int = 30
    VAD_AGGRESSIVENESS: int = 3
    SILENCE_DURATION_MS: int = 800
    PRE_SPEECH_BUFFER_MS: int = 500
    
    # === STT ===
    STT_MODEL_SIZE: str = "base"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "float32"
    
    # === LLM (Groq) ===
    LLM_MODEL: str = "llama-3.3-70b-versatile" 
    LLM_MAX_TOKENS: int = 150
    LLM_TEMPERATURE: float = 0.5

    # === GUI ===
    WINDOW_WIDTH: int = 400
    WINDOW_HEIGHT: int = 250
    WINDOW_OPACITY: float = 0.85
    UPDATE_INTERVAL_MS: int = 100
    QUEUE_MAX_SIZE: int = 10
    
    @property
    def chunk_samples(self) -> int:
        return int(self.SAMPLE_RATE * self.CHUNK_DURATION_MS / 1000)
    
    @property
    def silence_chunks(self) -> int:
        return int(self.SILENCE_DURATION_MS / self.CHUNK_DURATION_MS)
    
    @property
    def pre_speech_chunks(self) -> int:
        return int(self.PRE_SPEECH_BUFFER_MS / self.CHUNK_DURATION_MS)

CONFIG = Config()