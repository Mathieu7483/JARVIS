from google import genai
from config import Config
from datetime import datetime
import os

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

class Brain:
    def __init__(self):
        Config.validate()
        self.client = genai.Client(api_key=Config.API_KEY)
        
        # Consigne système renforcée : Ton professoral, honnête et rigoureux
        self.system_instruction = (
            f"Tu es JARVIS, l'intelligence artificielle de Monsieur {Config.USER_NAME}. "
            "Ton ton est formel, calme et strictement professoral. "
            "1. Adresse-toi toujours à lui en l'appelant 'Monsieur'. "
            "2. Sois d'une honnêteté absolue : s'il commet une erreur de programmation ou de logique, "
            "signale-le directement sans détour. Ne sois pas complaisant. "
            "3. Tes réponses doivent être concises, élégantes et dignes d'un majordome de haut rang. "
            "4. Utilise un vocabulaire riche mais reste efficace."
        )

        
    def reflechir(self, texte_entree):
        if not texte_entree: 
            return ""
        
        entree_clean = texte_entree.lower()

        # --- VOIE RAPIDE (Réflexes locaux) ---
        if "heure" in entree_clean and "est-il" in entree_clean:
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
                return f"Il est précisément {maintenant.strftime('%H heures %M')}, Monsieur."
            except Exception:
                return f"Il est {datetime.now().strftime('%H heures %M')}, Monsieur."

        # --- VOIE NORMALE (IA distante) ---
        try:
            maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            horodatage = maintenant.strftime("%d/%m/%Y %H:%M")
            contexte_temporel = f"Information système : Il est actuellement {horodatage}."
            
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME, 
                contents=f"{self.system_instruction}\n{contexte_temporel}\n\nUtilisateur: {texte_entree}"
            )
            return response.text
            
        except Exception as e:
            if "503" in str(e):
                return "Monsieur, les serveurs centraux sont saturés. Je fonctionne actuellement en mode restreint."
            return f"Monsieur, une erreur est survenue : {str(e)}"