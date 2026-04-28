"""
stt_engine.py
Transcripción de audio a texto usando faster-whisper (local).
"""
import io
import wave
import tempfile
import os
from typing import Optional
from faster_whisper import WhisperModel
from config import CONFIG


class STTEngine:
    """
    Motor de transcripción usando faster-whisper para procesamiento local.
    Baja latencia con modelos pequeños (tiny/base).
    """
    
    def __init__(self):
        print(f"[STT] Cargando modelo '{CONFIG.STT_MODEL_SIZE}'...")
        
        self.model = WhisperModel(
            CONFIG.STT_MODEL_SIZE,
            device=CONFIG.STT_DEVICE,
            compute_type=CONFIG.STT_COMPUTE_TYPE
        )
        print("[STT] ✅ Modelo cargado")
    
    def _bytes_to_wav(self, audio_bytes: bytes) -> str:
        """
        Convierte bytes de audio raw a archivo WAV temporal.
        faster-whisper necesita un archivo o numpy array.
        """
        # Crear archivo WAV en memoria
        with io.BytesIO() as wav_io:
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(CONFIG.SAMPLE_RATE)
                wav_file.writeframes(audio_bytes)
            
            wav_data = wav_io.getvalue()
        
        # Guardar temporalmente (faster-whisper acepta path)
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.write(wav_data)
        temp_file.close()
        
        return temp_file.name
    
    def transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe un segmento de audio a texto.
        Retorna None si no hay texto detectado.
        """
        if len(audio_bytes) < 1000:  # Muy corto
            return None
        
        temp_path = None
        try:
            temp_path = self._bytes_to_wav(audio_bytes)
            
            # Transcribir con faster-whisper
            segments, info = self.model.transcribe(
                temp_path,
                beam_size=5,
                best_of=5,
                condition_on_previous_text=False,  # Más rápido
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                language="es"  # <-- AQUÍ FORZAMOS EL ESPAÑOL
            )
            
            # Extraer texto de todos los segmentos
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            text = ' '.join(text_parts).strip()
            
            if text:
                print(f"[STT] 📝 Transcripción: '{text[:80]}...' " if len(text) > 80 else f"[STT] 📝 Transcripción: '{text}'")
                return text
            return None
            
        except Exception as e:
            print(f"[STT] ❌ Error: {e}")
            return None
            
        finally:
            # Limpiar archivo temporal
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)