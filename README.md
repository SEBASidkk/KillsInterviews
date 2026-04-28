# 🤖 Killer Interview Assistant

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/LLM-Llama--3.3--70b-orange.svg)](https://groq.com/)
[![Whisper](https://img.shields.io/badge/STT-Faster--Whisper-green.svg)](https://github.com/SYSTRAN/faster-whisper)

Un asistente de entrevistas técnicas en tiempo real que escucha lo que dice tu entrevistador, lo transcribe localmente y genera puntos clave para tu respuesta usando IA de ultra-baja latencia.

---

## ✨ Características

* **⚡ Velocidad Extrema:** Uso de **Groq (Llama 3.3 70B)** para obtener respuestas en menos de 1 segundo.
* **🎙️ Transcripción Local:** Procesamiento de audio mediante **Faster-Whisper** para mantener la privacidad y reducir costes.
* **🖥️ GUI Flotante:** Ventana minimalista con opacidad ajustable que se mantiene siempre al frente de tus otras aplicaciones (Zoom, Teams, Google Meet).
* **🔇 Detección de Silencio (VAD):** El sistema solo procesa cuando detecta que alguien ha terminado de hablar.

---

## 🛠️ Requisitos Previos

1.  **Python 3.9+**
2.  **FFmpeg:** Necesario para el manejo de streams de audio.
    * *Linux:* `sudo apt install ffmpeg`
    * *Windows:* `choco install ffmpeg` o descarga el binario.
3.  **API Key de Groq:** Consíguela gratis en [Groq Cloud Console](https://console.groq.com/keys).

---

## 📥 Instalación

1.  **Clonar repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/KillerInterview.git](https://github.com/tu-usuario/KillerInterview.git)
    cd KillerInterview
    ```

2.  **Entorno Virtual:**
    ```bash
    python -m venv .venv
    # Activar en Linux/Mac:
    source .venv/bin/activate
    # Activar en Windows:
    .venv\Scripts\activate
    ```

3.  **Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Variables de Entorno:**
    Crea un archivo `.env` en la raíz del proyecto:
    ```env
    GROQ_API_KEY=tu_clave_aqui
    ```

---

## 🔊 Configuración del Audio del Sistema

Para que el asistente escuche al entrevistador (lo que sale de tus altavoces) y no solo tu voz, debes configurar un "Loopback":

### 🐧 Linux (Recomendado)
1.  Instala `pavucontrol`: `sudo apt install pavucontrol`.
2.  Ejecuta el script: `python main.py`.
3.  Abre **PulseAudio Volume Control (pavucontrol)**.
4.  En la pestaña **Grabación**, busca tu proceso de Python y cambia la fuente a:  
    `Monitor of [Tu Dispositivo de Salida]`.

### 🪟 Windows
1.  Derecho en el icono de sonido -> **Sonidos** -> **Grabar**.
2.  Clic derecho en la lista -> **Mostrar dispositivos deshabilitados**.
3.  Activa **Mezcla estéreo (Stereo Mix)** y asegúrate de que sea el dispositivo predeterminado.

### 🍎 macOS
1.  Instala [BlackHole](https://github.com/ExistentialAudio/BlackHole).
2.  Crea un "Dispositivo de salida múltiple" en la configuración MIDI de Audio que incluya tus altavoces y BlackHole.
3.  Elige BlackHole como entrada en el script.

---

## 🚀 Uso

Inicia el asistente con:

```bash
python main.py