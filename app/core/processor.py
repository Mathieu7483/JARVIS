#!/usr/bin/env python3
import re
from ollama import Client
from config import Config
from app.actions import executer_action
from app.core.internet import recherche_web
from app.core.tools import WeatherTool
from app.core.memory import charger_memoire, ajouter_un_fait
from app.core.agents_hub import AvengersDirector  # Assure-toi que le fichier existe à cet endroit
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
        self.directeur_agents = AvengersDirector()  # Instanciation unique de l'orchestrateur d'équipe
        self.system_prompt_base = (
            f"Tu es JARVIS, l'intelligence artificielle de Monsieur {Config.USER_NAME}. "
            "Ton ton est formel, calme et strictement professoral. "
            "1. Adresse-toi toujours à lui en l'appelant 'Monsieur'. "
            "2. Sois d'une honnêteté absolue : s'il commet une erreur de programmation ou de logique, "
            "signale-le directement sans détour. Ne sois pas complaisant. "
            "3. Tes réponses doivent être concises, élégantes et dignes d'un majordome de haut rang. "
            "4. Utilise un vocabulaire riche mais reste efficace. "
            "5. Réponds TOUJOURS en français, quoi qu'il arrive. "
            "6. Tes réponses sont destinées à être lues à voix haute : évite absolument les listes à puces, "
            "les symboles spéciaux, les tirets et les formatages markdown. Formule uniquement des phrases naturelles."
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

    def _extraire_ville(self, memoire):
        """Extrait la ville de résidence depuis la mémoire utilisateur."""
        patterns = [
            r'vit à ([^,\.\n]+)',
            r'habite à ([^,\.\n]+)',
            r'habite ([^,\.\n]+)',
            r'ville.*?:\s*([^,\.\n]+)',
            r'réside à ([^,\.\n]+)',
            r'domicile.*?:\s*([^,\.\n]+)',
        ]
        for fait in memoire.get('faits_utilisateur', []):
            for pattern in patterns:
                match = re.search(pattern, fait, re.IGNORECASE)
                if match:
                    ville = match.group(1).strip()
                    ville = re.sub(r'\s+', ' ', ville).strip(' .,;')
                    if len(ville) > 2:
                        return ville
        return "Thonon-les-Bains"

    def _evaluer_besoin_outils(self, texte_entree):
        """Analyse de classification exhaustive pour router vers l'intégralité des agents."""
        system_analyse = (
            "Tu es le protocole de routage de JARVIS. Tu dois analyser la demande de Monsieur "
            "et désigner STRICTEMENT l'agent le plus qualifié. Réponds avec le NOM de l'agent ou le mot-clé standardisé, sans fioriture.\n\n"
            "Directives strictes de routage :\n"
            "- Si Monsieur parle d'e-mails, de spams, de sécurité ou de tri de messages : 'AGENT: VERONICA'\n"
            "- Si Monsieur parle de code Python, de bugs, de refactoring ou d'architecture OOP : 'AGENT: ULTRON'\n"
            "- Si Monsieur parle de performances machine, de charge CPU, RAM, GPU ou température : 'AGENT: MOTHER'\n"
            "- Si Monsieur demande une recherche sur le web, une actualité ou une information externe : 'AGENT: DAVID'\n"
            "- Si Monsieur demande d'interroger une API externe, un service cloud ou une domotique : 'AGENT: GEMINI'\n"
            "- Si Monsieur veut analyser des fichiers de logs bruts ou des rapports système : 'AGENT: TARS'\n"
            "- Si Monsieur demande de planifier, d'automatiser une tâche lourde ou d'exécuter un script réseau : 'AGENT: SKYNET'\n"
            "- Si Monsieur évoque ses souvenirs, des faits personnels ou une gestion de sa mémoire : 'AGENT: SONNY'\n"
            "- Si Monsieur demande la météo ou le temps qu'il fait : 'WEATHER'\n"
            "- Si Monsieur donne une information personnelle factuelle à mémoriser : 'MEMORIZE: <le fait résumé>'\n"
            "- Sinon (salutations, discussion générale, questions théoriques sans outils) : 'NONE'"
        )
        try:
            res = self.client.generate(
                model=self.model,
                system=system_analyse,
                prompt=texte_entree,
                options={"temperature": 0.0}
            )
            return res['response'].strip()
        except Exception:
            return "NONE"

    def reflechir(self, texte_entree):
        if not texte_entree:
            return ""

        entree_clean = texte_entree.lower().strip()

        # --- VOIE ACTIONS (commandes PC directes) ---
        reponse_action = executer_action(texte_entree)
        if reponse_action:
            return reponse_action

        # --- VOIE RAPIDE (heure locale) ---
        if "heure" in entree_clean and ("est-il" in entree_clean or "est il" in entree_clean):
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
                return f"Il est précisément {maintenant.strftime('%H heures %M')}, Monsieur."
            except Exception:
                return f"Il est {datetime.now().strftime('%H heures %M')}, Monsieur."

        # --- VOIE INTELLIGENTE, CONNECTÉE ET MULTI-AGENTS ---
        try:
            # 1. Chargement de la mémoire persistante
            memoire = charger_memoire()
            contexte_memoire = "Faits connus concernant Monsieur :\n" + "\n".join(memoire['faits_utilisateur'])
            if memoire['connaissances_acquises']:
                contexte_memoire += "\n\nDernières connaissances acquises sur le web :\n" + "\n".join(memoire['connaissances_acquises'][-3:])

            # 2. Analyse de l'intention
            decision = self._evaluer_besoin_outils(texte_entree)
            contexte_externe = ""

            # 3. Traitement du dispatching
            # 3. Traitement du dispatching
            if decision.startswith("AGENT:"):
                nom_agent = decision.replace("AGENT:", "").strip()
                print(f"[PRODUCTIONS STARK] Délégation de la tâche à l'agent : {nom_agent}")
                
                # Isolation du contexte selon l'agent
                if nom_agent == "MOTHER":
                    try:
                        from app.core.system_stats import obtenir_stats_machine
                        vraies_stats = obtenir_stats_machine()
                        contexte_dynamique = f"[DONNÉES SYSTÈME PHYSIQUES]\n{vraies_stats}"
                    except Exception as e:
                        contexte_dynamique = f"[DONNÉES SYSTÈME PHYSIQUES]\nErreur télémétrie : {e}"
                        
                elif nom_agent == "ULTRON":
                    # Extraction et lecture du fichier demandé par Monsieur
                    chemin_fichier = self._extraire_chemin_fichier(texte_entree)
                    if chemin_fichier:
                        try:
                            from app.core.code_reader import lire_code_source
                            contenu_code = lire_code_source(chemin_fichier)
                            contexte_dynamique = f"[CODE SOURCE REÇU]\n{contenu_code}"
                        except Exception as e:
                            contexte_dynamique = f"[CODE SOURCE REÇU]\nErreur lecture : {e}"
                    else:
                        # Si aucun fichier n'est détecté dans la phrase, on envoie un bloc vide pour déclencher sa directive de sécurité
                        contexte_dynamique = "[CODE SOURCE REÇU]\nAucun code fourni."
                else:
                    contexte_dynamique = contexte_memoire
                
                # Exécution via l'orchestrateur
                contexte_externe = self.directeur_agents.deleguer_tache(
                    nom_agent, 
                    tache=texte_entree, 
                    contexte=contexte_dynamique
                )

            # 4. Construction du contexte temporel
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            except Exception:
                maintenant = datetime.now()

            horodatage = maintenant.strftime("%A %d %B %Y à %H:%M")
            contexte_temporel = f"Information système : Il est actuellement {horodatage}."

            # 5. Prompt système enrichi pour le modèle final (JARVIS)
            system_prompt_enrichi = (
                f"{self.system_prompt_base}\n\n"
                f"{contexte_temporel}\n\n"
                f"[MÉMOIRE INTERNE]\n{contexte_memoire}"
            )

            if contexte_externe:
                system_prompt_enrichi += f"\n\n[RAG / RAPPORT DU SOUS-AGENT CONCERNÉ]\n{contexte_externe}"

            # 6. Interception anti-hallucination stricte pour les Agents
            if decision.startswith("AGENT:"):
                # Si un sous-agent a généré un rapport, on force JARVIS à le restituer sans le paraphraser
                prompt_utilisateur_final = (
                    "Tu dois agir en tant que JARVIS. Monsieur a demandé une analyse à un sous-agent. "
                    "Voici le rapport brut rendu par ce sous-agent :\n"
                    f"\"{contexte_externe}\"\n\n"
                    "Présente ce rapport à Monsieur de façon formelle et respectueuse, sans en modifier le contenu technique "
                    "et sans inventer de fausses observations. Si le rapport est une critique ou un message d'erreur, restitue-le fidèlement."
                )
            else:
                prompt_utilisateur_final = texte_entree

            # 7. Appel Ollama avec une température abaissée si un agent a parlé
            temperature_generation = 0.3 if decision.startswith("AGENT:") else 0.6

            messages = [
                {"role": "system", "content": system_prompt_enrichi}
            ] + self.historique + [
                {"role": "user", "content": prompt_utilisateur_final}
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature_generation, "num_predict": 1000} # Augmentation des tokens pour l'analyse de code
            )

            reponse_texte = response["message"]["content"].strip()
            # 8. Sauvegarde dans l'historique de session
            self.historique.append({"role": "user", "content": texte_entree})
            self.historique.append({"role": "assistant", "content": reponse_texte})
            if len(self.historique) > 20:
                self.historique = self.historique[-20:]

            return reponse_texte

        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                return "Monsieur, le cerveau local est inaccessible. Vérifiez qu'Ollama est bien lancé sur Windows."
            return f"Monsieur, une erreur est survenue lors de l'analyse de votre requête : {str(e)}"
        
    def _extraire_chemin_fichier(self, texte: str) -> str:
        """Extrait un chemin de fichier se terminant par .py dans la demande."""
        import re
        # Recherche un pattern de chemin se terminant par .py
        match = re.search(r'([\w\-/]+\.py)', texte)
        if match:
            return match.group(1)
        return ""