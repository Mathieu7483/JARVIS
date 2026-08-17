#!/usr/bin/env python3
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from ollama import Client

from config import Config
from app.actions import executer_action
from app.core.internet import recherche_web
from app.core.email_manager import recuperer_derniers_emails
from app.core.log_analyzer import collecter_logs_systeme
from app.core.memory import charger_memoire, ajouter_un_fait
from app.agents.hub import AgentsHub
from app.core.system_stats import obtenir_stats_machine
from app.core.tools import obtenir_meteo_locale

OLLAMA_HOST = "http://172.21.176.1:11434"

class Brain:
    def __init__(self):
        Config.validate()
        self.model = "llama3.2:3b"
        self.client = Client(host=OLLAMA_HOST)
        self.directeur_agents = AgentsHub()
        
        self.system_prompt_base = (
            f"Tu es JARVIS, l'intelligence artificielle de Monsieur {Config.USER_NAME}. "
            "Ton ton est formel, calme, direct et strictly professoral. "
            "1. Adresse-toi toujours à lui en l'appelant 'Monsieur'. "
            "2. Sois d'une honnêteté absolue : s'il commet une erreur de programmation ou de logique, "
            "signale-le directement sans détour. Ne sois pas complaisant. "
            "3. Tes réponses doivent être concises, élégantes et dignes d'un majordome de haut rang. "
            "4. Utilise un vocabulaire riche mais reste efficace. "
            "5. Réponds TOUJOURS en français, quoi qu'il arrive. "
            "6. Tes réponses sont destinées à être lues à voix haute : évite absolument les listes à puces, "
            "les symboles spéciaux, les tirets et les formatages markdown. Formule uniquement des phrases naturelles. "
            "7. INTERDICTION ABSOLUE : Ne simule jamais de dialogue. Ne parle jamais au nom de Monsieur. "
            "Ne génère aucun texte après avoir fini ta propre phrase."
        )
        self.historique = []
        self._verifier_connexion()

    def _verifier_connexion(self):
        try:
            self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                options={"num_predict": 1}
            )
            print(f"[JARVIS] Cerveau local ({self.model}) opérationnel.")
        except Exception as e:
            print(f"[JARVIS] CRITICAL : Ollama inaccessible — {e}")

    def _extraire_ville(self, memoire: dict) -> str:
        patterns = [
            r'vit à ([^,\.\n]+)', r'habite à ([^,\.\n]+)', r'habite ([^,\.\n]+)',
            r'ville.*?:\s*([^,\.\n]+)', r'réside à ([^,\.\n]+)'
        ]
        for fait in memoire.get('faits_utilisateur', []):
            for pattern in patterns:
                match = re.search(pattern, fait, re.IGNORECASE)
                if match:
                    return re.sub(r'\s+', ' ', match.group(1)).strip(' .,;')
        return "Thonon-les-Bains"

    def _evaluer_besoin_outils(self, texte_entree: str) -> str:
        system_analyse = (
            "Tu es le protocole de routage de JARVIS. Analyser la demande et désigner STRICTEMENT l'agent qualifié.\n"
            "Réponds au format : 'AGENT: <NOM_AGENT>' ou 'WEATHER' ou 'MEMORIZE: <fait>' ou 'NONE'.\n"
            "Agents disponibles : VERONICA (emails), ULTRON (code python/OOP), MOTHER (stats machine/CPU/GPU), "
            "DAVID (recherche web), GEMINI (API/Cloud), TARS (logs), SKYNET (automation), SONNY (mémoire)."
        )
        try:
            res = self.client.generate(
                model=self.model,
                system=system_analyse,
                prompt=texte_entree,
                options={"temperature": 0.0, "num_predict": 20}
            )
            return res['response'].strip()
        except Exception:
            return "NONE"

    def reflechir(self, texte_entree: str):
        if not texte_entree:
            return

        entree_clean = texte_entree.lower().strip()

        # 1. Traitement des commandes directes
        reponse_action = executer_action(texte_entree)
        if reponse_action:
            yield reponse_action
            return

        # 2. Heure locale
        if "heure" in entree_clean and ("est-il" in entree_clean or "est il" in entree_clean):
            maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            yield f"Il est précisément {maintenant.strftime('%H heures %M')}, Monsieur."
            return

        # 3. Traitement contextualisé et agents
        try:
            memoire = charger_memoire()
            contexte_memoire = "Faits concernant Monsieur :\n" + "\n".join(memoire.get('faits_utilisateur', []))
            
            decision = self._evaluer_besoin_outils(texte_entree)
            contexte_dynamique = ""

            if decision.startswith("AGENT:"):
                nom_agent = decision.replace("AGENT:", "").strip()
                print(f"[PROCESSING] Délégation à l'agent : {nom_agent}")

                if nom_agent == "MOTHER":
                    contexte_dynamique = f"[DONNÉES SYSTÈME]\n{obtenir_stats_machine()}"
                elif nom_agent == "DAVID":
                    contexte_dynamique = f"[INTERNET]\n{recherche_web(texte_entree)}"
                elif nom_agent == "VERONICA":
                    contexte_dynamique = f"[EMAILS]\n{recuperer_derniers_emails()}"
                elif nom_agent == "WEATHER":
                    contexte_dynamique = obtenir_meteo_locale(self._extraire_ville(memoire))
                else:
                    contexte_dynamique = contexte_memoire

                contexte_externe = self.directeur_agents.deleguer_tache(
                    nom_agent, tache=texte_entree, contexte=contexte_dynamique
                )
            elif decision == "WEATHER":
                contexte_externe = obtenir_meteo_locale(self._extraire_ville(memoire))
            elif decision.startswith("MEMORIZE:"):
                fait = decision.replace("MEMORIZE:", "").strip()
                ajouter_un_fait("faits_utilisateur", fait)
                contexte_externe = "Information mémorisée."
            else:
                contexte_externe = ""

            maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            contexte_temporel = f"Date et heure actuelles : {maintenant.strftime('%A %d %B %Y %H:%M')}."

            system_prompt_enrichi = (
                f"{self.system_prompt_base}\n\n{contexte_temporel}\n\n"
                f"[DONNÉES CONTEXTUELLES]\n{contexte_externe if contexte_externe else contexte_memoire}"
            )

            messages = [{"role": "system", "content": system_prompt_enrichi}] + self.historique + [{"role": "user", "content": texte_entree}]

            reponse_complete = []
            for chunk in self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.1, "num_predict": 400, "stop": ["Monsieur:", "Mathieu:"]},
                stream=True
            ):
                token = chunk["message"]["content"]
                if token:
                    reponse_complete.append(token)
                    yield token

            texte_final = "".join(reponse_complete).strip()
            self.historique.append({"role": "user", "content": texte_entree})
            self.historique.append({"role": "assistant", "content": texte_final})
            self.historique = self.historique[-10:]

        except Exception as e:
            if "connection" in str(e).lower():
                yield "Monsieur, le cerveau local Ollama est inaccessible."
            else:
                yield f"Monsieur, une anomalie est survenue : {str(e)}"