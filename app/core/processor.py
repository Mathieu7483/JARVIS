#!/usr/bin/env python3
import re
from ollama import Client
from config import Config
from app.actions import executer_action
from app.core.internet import recherche_web
from app.core.email_manager import recuperer_derniers_emails
from app.core.log_analyzer import collecter_logs_systeme
from app.core.api_connector import executer_requete_api
from app.core.tools import WeatherTool
from app.core.memory import charger_memoire, ajouter_un_fait
from app.core.agents_hub import AvengersDirector
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
        self.directeur_agents = AvengersDirector()  # Orchestrateur d'équipe
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

    def _extraire_chemin_fichier(self, texte: str) -> str:
        """Extrait un chemin de fichier se terminant par une extension connue pour l'agent ULTRON."""
        match = re.search(r'([\w\-/]+\.(?:py|log|txt|js|html|css))', texte, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def _evaluer_besoin_outils(self, texte_entree):
        """Analyse de classification exhaustive pour router vers l'integralité des agents."""
        system_analyse = (
            "Tu es le protocole de routage de JARVIS. Tu devez analyser la demande de Monsieur "
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

    def reflechir(self, texte_entree: str) -> str:
        if not texte_entree:
            return ""

        # --- PURGE ET RÉINITIALISATION STRICTE DU CONTEXTE ---
        contexte_externe = ""
        contexte_dynamique = ""
        decision = ""
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
            decision = self._evaluer_besoin_outils(entree_clean)

            # 3. Traitement du dispatching
            if decision.startswith("AGENT:"):
                nom_agent = decision.replace("AGENT:", "").strip()
                print(f"[PROCESSING] Délégation de la tâche à l'agent : {nom_agent}")
                
                # --- ISOLATION ET REMPLISSAGE DU CONTEXTE DYNAMIQUE ---
                if nom_agent == "MOTHER":
                    try:
                        from app.core.system_stats import obtenir_stats_machine
                        vraies_stats = obtenir_stats_machine()
                        contexte_dynamique = f"[DONNÉES SYSTÈME PHYSIQUES]\n{vraies_stats}"
                    except Exception as e:
                        contexte_dynamique = f"[DONNÉES SYSTÈME PHYSIQUES]\nErreur télémétrie : {e}"
                        
                elif nom_agent == "ULTRON":
                    chemin_fichier = self._extraire_chemin_fichier(texte_entree)
                    if chemin_fichier:
                        try:
                            from app.core.code_reader import lire_code_source
                            contenu_code = lire_code_source(chemin_fichier)
                            contexte_dynamique = f"[CODE SOURCE REÇU]\n{contenu_code}"
                        except Exception as e:
                            contexte_dynamique = f"[CODE SOURCE REÇU]\nErreur lecture : {e}"
                    else:
                        contexte_dynamique = "[CODE SOURCE REÇU]\nAucun code fourni."

                elif nom_agent == "DAVID":
                    sujet = entree_clean
                    for mot in ["jarvis", "demande à david", "quelles sont", "les dernières", "nouvelles de", "la mise à jour de"]:
                        sujet = sujet.replace(mot, "")
                    
                    sujet = re.sub(r"[',\.?!\";:]", " ", sujet)
                    sujet = " ".join(sujet.split())
                    
                    annee_actuelle = datetime.now().strftime("%Y")
                    if "cette année" in entree_clean or "dernières" in entree_clean:
                        if annee_actuelle not in sujet:
                            sujet += f" {annee_actuelle}"
                    
                    if not sujet:
                        sujet = f"python programming language updates {annee_actuelle}"

                    resultats_internet = recherche_web(sujet)
                    
                    print("\n" + "="*40)
                    print(f"[DEBUG MATRIX] Contenu internet envoyé à DAVID (Sujet: '{sujet}') :\n{resultats_internet}")
                    print("="*40 + "\n")
                    
                    contexte_dynamique = f"[CONTEXTE INTERNET FOURNI]\n{resultats_internet}"

                elif nom_agent == "VERONICA":
                    flux_emails = recuperer_derniers_emails()
                    
                    print("\n" + "="*40)
                    print(f"[DEBUG MATRIX] Flux e-mails envoyé à VERONICA : '{flux_emails}'")
                    print("="*40 + "\n")
                    
                    if not flux_emails or flux_emails.strip() == "":
                        contexte_dynamique = "[ALERTE SYSTÈME CRITIQUE]\nAucun e-mail reçu. Flux vide."
                    else:
                        contexte_dynamique = f"[E-MAILS RÉELS REÇUS]\n{flux_emails}"
                
                elif nom_agent == "TARS":
                    chemin_cible = "flask_access.log"
                    match = re.search(r'([\w\-/]+\.(?:log|txt))', texte_entree.lower())
                    if match:
                        chemin_cible = match.group(1)
                    
                    donnees_brutes = collecter_logs_systeme(chemin_cible)
                    
                    print("\n" + "="*40)
                    print(f"[DEBUG MATRIX] Données brutes envoyées à TARS :\n{donnees_brutes}")
                    print("="*40 + "\n")
                    
                    contexte_dynamique = f"[FLUX DE LOGS SYSTEME]\n{donnees_brutes}"

                elif nom_agent == "GEMINI":
                    url_cible = "https://api.inconnue.com/v1/status"
                    match = re.search(r'(https?://[^\s]+)', texte_entree)
                    if match:
                        url_cible = match.group(1)
                        
                    flux_api = executer_requete_api(url_cible)
                    
                    print("\n" + "="*40)
                    print(f"[DEBUG MATRIX] Payload reçu envoyé à GEMINI :\n{flux_api}")
                    print("="*40 + "\n")
                    
                    contexte_dynamique = f"[RETOUR PASSERELLE API]\n{flux_api}"
                    
                else:
                    contexte_dynamique = contexte_memoire
                
                # Exécution via l'orchestrateur de l'équipe
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

            # 5. Prompt système enrichi pour JARVIS avec isolation hermétique
            if decision.startswith("AGENT:"):
                # Nettoyage total : aucune fuite de la mémoire interne globale vers l'évaluation de l'agent
                system_prompt_enrichi = f"{self.system_prompt_base}\n\n{contexte_temporel}"
                if contexte_externe:
                    system_prompt_enrichi += f"\n\n[RAG / RAPPORT DU SOUS-AGENT CONCERNÉ]\n{contexte_externe}"
            else:
                # Discussion théorique classique : chargement standard de la mémoire
                system_prompt_enrichi = (
                    f"{self.system_prompt_base}\n\n"
                    f"{contexte_temporel}\n\n"
                    f"[MÉMOIRE INTERNE]\n{contexte_memoire}"
                )

            # 6. Interception anti-hallucination stricte pour les Agents
            if decision.startswith("AGENT:"):
                prompt_utilisateur_final = (
                    "Tu es JARVIS. Tu devez synthétiser le rapport brut du sous-agent pour Monsieur. "
                    "CONSIGNES ABSOLUES DE FORMALISME :\n"
                    "1. INTERDICTION FORMELLE d'utiliser du markdown, des listes, des tirets, des étoiles ou des puces. Uniquement des phrases rédigées.\n"
                    "2. Supprime toutes les conclusions génériques de chatbot (ex: 'Je reste à votre disposition', 'Il convient d'enquêter'). Va droit au but.\n"
                    "CONSIGNES TECHNIQUES LOGIQUES :\n"
                    "3. L'adresse IP 172.21.176.1 correspond à la machine locale de Monsieur (WSL). Ne la qualifie JAMAIS de suspecte. C'est le trafic normal du serveur.\n"
                    "4. Traduis les faits de manière brute : une série de codes 401 sur un admin est un brute-force. Un code 500 est une erreur de code serveur.\n\n"
                    "Voici le rapport brut à nettoyer et fluidifier :\n"
                    f"\"{contexte_externe}\""
                )
            else:
                prompt_utilisateur_final = texte_entree

            # --- CONFIGURATION DES VARIABLES ET ISOLATION ---
            temperature_generation = 0.1 if decision.startswith("AGENT:") else 0.6

            if decision.startswith("AGENT:"):
                messages = [
                    {"role": "system", "content": system_prompt_enrichi},
                    {"role": "user", "content": prompt_utilisateur_final}
                ]
            else:
                messages = [
                    {"role": "system", "content": system_prompt_enrichi}
                ] + self.historique + [
                    {"role": "user", "content": prompt_utilisateur_final}
                ]

            # Appel Ollama final
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature_generation, "num_predict": 1000}
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