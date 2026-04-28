"""
llm_processor.py
Procesa transcripciones usando Groq (Llama 3) para máxima velocidad.
"""
import os
from groq import Groq
from typing import Optional
from config import CONFIG
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class LLMProcessor:
    """
    Procesa texto transcrito y genera 3 puntos clave usando Llama 3 en Groq.
    """
    
    SYSTEM_PROMPT = """Eres un asistente de entrevistas técnicas. 
Tu trabajo es analizar lo que dice el entrevistador y dar puntos clave de respuesta.

REGLAS:
- Responde EXACTAMENTE con 3 bullet points.
- Cada bullet debe ser corto (máximo 15 palabras).
- Sé muy conciso.
- Formato: • [punto clave]"""

    def __init__(self):
        # Obtener la API Key desde el entorno
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("❌ ERROR: GROQ_API_KEY no encontrada en el archivo .env")
            
        # Inicializar el cliente de Groq
        self.client = Groq(api_key=api_key)
        print(f"[LLM] ✅ Cliente Groq inicializado (Modelo: {CONFIG.LLM_MODEL})")
    
    def process(self, transcript: str) -> Optional[str]:
        """
        Envía la transcripción a Groq y retorna 3 bullets de respuesta.
        """
        if not transcript or len(transcript) < 5:
            return None
        
        try:
            print(f"[LLM] 🚀 Enviando a Groq...")
            
            # Llamada a la API de Groq
            completion = self.client.chat.completions.create(
                model=CONFIG.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Entrevistador dice: {transcript}"}
                ],
                max_tokens=CONFIG.LLM_MAX_TOKENS,
                temperature=CONFIG.LLM_TEMPERATURE,
            )
            
            # Extraer la respuesta
            bullets = completion.choices[0].message.content.strip()
            
            # Limpieza básica para asegurar que solo devuelva los bullets
            bullets = self._clean_response(bullets)
            
            print(f"[LLM] ✅ Respuesta recibida de Groq")
            return bullets
            
        except Exception as e:
            print(f"[LLM] ❌ Error con Groq: {e}")
            return None
            
    def _clean_response(self, text: str) -> str:
        """
        Asegura que no haya texto extra antes o después de los bullets.
        """
        lines = [line.strip() for line in text.split('\n') if '•' in line or line.strip().startswith('-') or line.strip().startswith('*')]
        if not lines:
            # Si no hay bullets claros, intentamos tomar las primeras 3 líneas
            lines = [line.strip() for line in text.split('\n') if line.strip()][:3]
            return '\n'.join([f"• {l.replace('- ', '').replace('* ', '')}" for l in lines])
            
        return '\n'.join(lines[:3])