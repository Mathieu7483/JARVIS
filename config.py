import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # On récupère la clé API (assure-toi qu'elle s'appelle API_KEY dans ton .env)
    API_KEY = os.getenv("API_KEY")
    USER_NAME = "Mathieu"
    ASSISTANT_NAME = "JARVIS"
    
    # LE MODÈLE VALIDÉ PAR TON CURL
    MODEL_NAME = "gemini-3-flash-preview" 
    
    # Paramètres audio
    LANGUAGE = "fr-FR"

    @classmethod
    def validate(cls):
        if not cls.API_KEY:
            raise ValueError("ERREUR : La clé API est manquante. Vérifiez votre fichier .env")
        print(f"[{cls.ASSISTANT_NAME}] : Connexion établie. Modèle : {cls.MODEL_NAME}")