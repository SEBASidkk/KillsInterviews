"""
audio_capture.py
Captura audio del sistema usando sounddevice y detecta fin de frase con VAD.
"""
import threading
import queue
import numpy as np
import sounddevice as sd
import webrtcvad
import collections
from typing import Optional
from config import CONFIG


class AudioCaptureThread(threading.Thread):
    """
    Hilo dedicado a capturar audio del sistema y detectar segmentos de voz.
    Usa un cable de audio virtual (VB-Audio/BlackHole) como entrada.
    """
    
    def __init__(self, transcript_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(name="AudioCapture", daemon=True)
        self.transcript_queue = transcript_queue
        self.stop_event = stop_event
        
        # Inicializar VAD (Voice Activity Detection)
        self.vad = webrtcvad.Vad(CONFIG.VAD_AGGRESSIVENESS)
        
        # Buffer circular para pre-speech audio
        self.ring_buffer = collections.deque(maxlen=CONFIG.pre_speech_chunks)
        
        # Estado de la máquina de estados
        self.triggered = False
        self.voiced_frames = []
        self.silence_counter = 0
        
        print(f"[Audio] Inicializado: {CONFIG.SAMPLE_RATE}Hz, chunk={CONFIG.CHUNK_DURATION_MS}ms")
    
    def _is_speech(self, audio_bytes: bytes) -> bool:
        """Verifica si el chunk contiene voz usando WebRTC VAD."""
        try:
            return self.vad.is_speech(audio_bytes, CONFIG.SAMPLE_RATE)
        except Exception as e:
            print(f"[Audio] Error VAD: {e}")
            return False
    
    def _normalize_audio(self, indata: np.ndarray) -> bytes:
        """
        Convierte audio float32 [-1, 1] a int16 bytes para VAD.
        """
        # Asegurar mono
        if indata.ndim > 1:
            indata = indata.mean(axis=1)
        
        # Convertir a int16
        audio_int16 = (indata * 32767).astype(np.int16)
        return audio_int16.tobytes()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback llamado por sounddevice en cada chunk."""
        if status:
            print(f"[Audio] Status: {status}")
        
        # Normalizar y convertir
        audio_bytes = self._normalize_audio(indata)
        
        # Máquina de estados: triggered / no triggered
        is_speech = self._is_speech(audio_bytes)
        
        if not self.triggered:
            # Estado: ESPERANDO VOZ
            self.ring_buffer.append(audio_bytes)
            
            if is_speech:
                # Inicio de voz detectado
                self.triggered = True
                self.voiced_frames = list(self.ring_buffer)
                self.silence_counter = 0
                print("[Audio] 🎤 Voz detectada - iniciando grabación")
                
        else:
            # Estado: GRABANDO VOZ
            self.voiced_frames.append(audio_bytes)
            
            if is_speech:
                self.silence_counter = 0
            else:
                self.silence_counter += 1
                
                if self.silence_counter > CONFIG.silence_chunks:
                    # Fin de frase detectado
                    self.triggered = False
                    
                    # Concatenar todos los frames
                    audio_segment = b''.join(self.voiced_frames)
                    
                    # Enviar a la queue de transcripción
                    try:
                        self.transcript_queue.put_nowait(audio_segment)
                        print(f"[Audio] 📤 Segmento enviado: {len(audio_segment)} bytes")
                    except queue.Full:
                        print("[Audio] ⚠️ Queue llena - descartando segmento")
                    
                    # Limpiar buffer
                    self.voiced_frames = []
                    self.ring_buffer.clear()
    
    def run(self):
        """Loop principal de captura."""
        print("[Audio] 🎧 Iniciando captura de audio...")
        print("[Audio] Asegúrate de que el cable virtual esté seleccionado como entrada")
        
        try:
            with sd.InputStream(  # <-- Solo quitamos la palabra "Raw"
                samplerate=CONFIG.SAMPLE_RATE,
                blocksize=CONFIG.chunk_samples,
                dtype='float32',
                channels=1,
                callback=self._audio_callback
            ):
                # Mantener el hilo vivo hasta señal de parada
                while not self.stop_event.is_set():
                    self.stop_event.wait(0.1)
                    
        except Exception as e:
            print(f"[Audio] ❌ Error: {e}")
            raise
        
        print("[Audio] 🛑 Captura detenida")