"""
main.py
Punto de entrada del Asistente de Entrevistas.
Orquesta los módulos asegurando que la GUI corra en el Hilo Principal.
"""
import os
import sys
import queue
import threading
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env (Importante para Groq)
load_dotenv()

# Nuestros módulos
from config import CONFIG
from audio_capture import AudioCaptureThread
from stt_engine import STTEngine
from llm_processor import LLMProcessor
from gui import FloatingWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer


class InterviewHelper:
    def __init__(self):
        self.stop_event = threading.Event()
        self.transcript_queue = queue.Queue(maxsize=CONFIG.QUEUE_MAX_SIZE)
        self.result_queue = queue.Queue(maxsize=CONFIG.QUEUE_MAX_SIZE)
        
        self.stt: Optional[STTEngine] = None
        self.llm: Optional[LLMProcessor] = None
        
        self.audio_thread: Optional[AudioCaptureThread] = None
        self.processing_thread: Optional[threading.Thread] = None
    
    def _processing_loop(self):
        """Hilo en segundo plano para STT → LLM"""
        print("[Processing] 🧠 Iniciando loop de procesamiento...")
        try:
            self.stt = STTEngine()
            self.llm = LLMProcessor()
        except Exception as e:
            print(f"[Processing] ❌ Error crítico al inicializar motores: {e}")
            return
        
        while not self.stop_event.is_set():
            try:
                # Esperar audio de la cola
                audio_bytes = self.transcript_queue.get(timeout=0.5)
                
                # 1. Transcribir (Whisper local)
                transcript = self.stt.transcribe(audio_bytes)
                if not transcript:
                    continue
                
                # 2. Procesar con LLM (Groq)
                bullets = self.llm.process(transcript)
                if not bullets:
                    continue
                
                # 3. Enviar a la cola de resultados para la GUI
                try:
                    self.result_queue.put_nowait(bullets)
                except queue.Full:
                    pass
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Processing] ❌ Error en el loop: {e}")
                
        print("[Processing] 🛑 Loop detenido")
    
    def start_background_tasks(self):
        """Inicia los hilos de audio y procesamiento"""
        # 1. Hilo de procesamiento
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            name="Processing",
            daemon=True
        )
        self.processing_thread.start()
        
        # 2. Hilo de audio
        self.audio_thread = AudioCaptureThread(
            self.transcript_queue, 
            self.stop_event
        )
        self.audio_thread.start()
        
        print("\n  🎧 Escuchando audio del sistema en segundo plano...")

    def stop_background_tasks(self):
        """Detiene los hilos cuando se cierra la ventana"""
        print("\n[Main] 🔄 Deteniendo servicios...")
        self.stop_event.set()
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        if self.processing_thread:
            self.processing_thread.join(timeout=2)


def main():
    print("=" * 60)
    print("  🤖 INTERVIEW HELPER - Asistente de Entrevistas (Groq Edition)")
    print("=" * 60)
    
    # Verificación de API Key de Groq
    if not os.getenv("GROQ_API_KEY"):
        print("\n❌ ERROR: GROQ_API_KEY no encontrada en el archivo .env")
        print("Obtén una en: https://console.groq.com/keys")
        sys.exit(1)

    helper = InterviewHelper()
    
    # La GUI DEBE estar en el hilo principal
    app = QApplication(sys.argv)
    
    # Iniciar hilos secundarios (Audio y Procesamiento)
    helper.start_background_tasks()
    
    # Configurar y mostrar la ventana flotante
    window = FloatingWindow()
    window.show()
    
    # Timer para revisar la cola de resultados y actualizar la GUI
    def check_queue():
        try:
            while not helper.result_queue.empty():
                result = helper.result_queue.get_nowait()
                window.update_bullets(result)
        except queue.Empty:
            pass

    timer = QTimer()
    timer.timeout.connect(check_queue)
    timer.start(CONFIG.UPDATE_INTERVAL_MS)
    
    # Manejar cierre seguro de hilos al cerrar la ventana
    def on_close():
        helper.stop_background_tasks()
        app.quit()
        
    app.aboutToQuit.connect(on_close)
    
    # Iniciar el loop de la interfaz
    sys.exit(app.exec())

if __name__ == "__main__":
    main()