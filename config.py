import os
from dotenv import load_dotenv
 
load_dotenv()
 
class Config:
    USER_NAME = "Mathieu"
    ASSISTANT_NAME = "JARVIS"
    LANGUAGE = "fr-FR"
 
    # Adresse d'Ollama sur Windows, accessible depuis WSL
    OLLAMA_HOST = "http://172.21.176.1:11434"
 
    @classmethod
    def validate(cls):
        print(f"[{cls.ASSISTANT_NAME}] : Cerveau local Ollama — {cls.OLLAMA_HOST}")
 