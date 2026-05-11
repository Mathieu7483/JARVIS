from ollama import Client
from config import Config
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

OLLAMA_HOST = "http://172.21.176.1:11434"

class Brain:
    def __init__(self):
        Config.validate()

        self.model = "llama3.1:8b"
        self.client = Client(host=OLLAMA_HOST)

        self.system_prompt = (
            f"Tu es JARVIS, l'intelligence artificielle de Monsieur {Config.USER_NAME}. "
            "Ton ton est formel, calme et strictement professoral. "
            "1. Adresse-toi toujours à lui en l'appelant 'Monsieur'. "
            "2. Sois d'une honnêteté absolue : s'il commet une erreur de programmation ou de logique, "
            "signale-le directement sans détour. Ne sois pas complaisant. "
            "3. Tes réponses doivent être concises, élégantes et dignes d'un majordome de haut rang. "
            "4. Utilise un vocabulaire riche mais reste efficace. "
            "5. Réponds TOUJOURS en français, quoi qu'il arrive. "
            "6. Tes réponses sont destinées à être lues à voix haute : évite les listes à puces, "
            "les symboles spéciaux et les formatages markdown. Formule des phrases naturelles."
        )

        self.historique = []

        try:
            self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                options={"num_predict": 1}
            )
            print(f"[JARVIS] Cerveau local ({self.model}) opérationnel.")
        except Exception as e:
            print(f"[JARVIS] Attention : Ollama inaccessible — {e}")
            print("[JARVIS] Vérifiez qu'Ollama est bien lancé sur Windows.")

    def reflechir(self, texte_entree):
        if not texte_entree:
            return ""

        entree_clean = texte_entree.lower()

        # --- VOIE RAPIDE ---
        if "heure" in entree_clean and ("est-il" in entree_clean or "est il" in entree_clean):
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
                return f"Il est précisément {maintenant.strftime('%H heures %M')}, Monsieur."
            except Exception:
                return f"Il est {datetime.now().strftime('%H heures %M')}, Monsieur."

        # --- VOIE OLLAMA ---
        try:
            maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            horodatage = maintenant.strftime("%d/%m/%Y %H:%M")
            contexte_temporel = f"Information système : Il est actuellement {horodatage}."

            messages = [
                {
                    "role": "system",
                    "content": f"{self.system_prompt}\n{contexte_temporel}"
                }
            ] + self.historique + [
                {
                    "role": "user",
                    "content": texte_entree
                }
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "num_predict": 300,
                }
            )

            reponse_texte = response["message"]["content"].strip()

            self.historique.append({"role": "user", "content": texte_entree})
            self.historique.append({"role": "assistant", "content": reponse_texte})
            if len(self.historique) > 20:
                self.historique = self.historique[-20:]

            return reponse_texte

        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                return "Monsieur, le cerveau local est inaccessible. Vérifiez qu'Ollama est bien lancé sur Windows."
            return f"Monsieur, une erreur est survenue : {str(e)}"