#!/usr/bin/env python3
import re
import asyncio
from ollama import AsyncClient
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
        self.client = AsyncClient(host=OLLAMA_HOST)
        self.directeur_agents = AvengersDirector()
        
        self.system_prompt_base = (
            f"Tu es JARVIS, l'intelligence artificielle de Monsieur {Config.USER_NAME}. "
            "Ton ton est formel, calme, direct et strictement professoral. "
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

    async def _verifier_connexion_ollama(self):
        try:
            await self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                options={"num_predict": 1}
            )
            print(f"[JARVIS] Cerveau local ({self.model}) opérationnel.")
        except Exception as e:
            print(f"[JARVIS] CRITICAL : Ollama inaccessible — {e}")

    def _extraire_ville(self, memoire):
        patterns = [
            r'vit à ([^,\.\n]+)', r'habite à ([^,\.\n]+)', r'habite ([^,\.\n]+)',
            r'ville.*?:\s*([^,\.\n]+)', r'réside à ([^,\.\n]+)', r'domicile.*?:\s*([^,\.\n]+)'
        ]
        for fait in memoire.get('faits_utilisateur', []):
            for pattern in patterns:
                match = re.search(pattern, fait, re.IGNORECASE)
                if match:
                    ville = match.group(1).strip()
                    return re.sub(r'\s+', ' ', ville).strip(' .,;')
        return "Thonon-les-Bains"

    def _extraire_chemin_fichier(self, texte: str) -> str:
        match = re.search(r'([\w\-/\.]+\.(?:py|log|txt|js|html|css))', texte, re.IGNORECASE)
        return match.group(1) if match else ""

    async def _evaluer_besoin_outils(self, texte_entree: str) -> str:
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
            res = await self.client.generate(
                model=self.model,
                system=system_analyse,
                prompt=texte_entree,
                options={"temperature": 0.0}
            )
            return res['response'].strip()
        except Exception:
            return "NONE"

    async def reflechir(self, texte_entree: str):
        if not texte_entree:
            return

        contexte_externe = ""
        contexte_dynamique = ""
        decision = ""
        entree_clean = texte_entree.lower().strip()

        # --- VOIE ACTIONS (OS Directes) ---
        reponse_action = executer_action(texte_entree)
        if reponse_action:
            yield reponse_action
            return

        # --- VOIE RAPIDE (Heure) ---
        if "heure" in entree_clean and ("est-il" in entree_clean or "est il" in entree_clean):
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
                yield f"Il est précisément {maintenant.strftime('%H heures %M')}, Monsieur."
            except Exception:
                yield f"Il est {datetime.now().strftime('%H heures %M')}, Monsieur."
            return

        # --- VOIE MULTI-AGENTS ---
        try:
            memoire = charger_memoire()
            contexte_memoire = "Faits connus concernant Monsieur :\n" + "\n".join(memoire['faits_utilisateur'])
            if memoire['connaissances_acquises']:
                contexte_memoire += "\n\nDernières connaissances acquises sur le web :\n" + "\n".join(memoire['connaissances_acquises'][-3:])

            decision = await self._evaluer_besoin_outils(entree_clean)

            if decision.startswith("AGENT:"):
                nom_agent = decision.replace("AGENT:", "").strip()
                print(f"[PROCESSING] Délégation de la tâche à l'agent spécialisé : {nom_agent}")
                
                self.historique = [] # Purge interférences
                
                if nom_agent == "MOTHER":
                    try:
                        from app.core.system_stats import obtenir_stats_machine
                        contexte_dynamique = f"[DONNÉES SYSTÈME PHYSIQUES]\n{obtenir_stats_machine()}"
                    except Exception as e:
                        contexte_dynamique = f"[DONNÉES SYSTÈME PHYSIQUES]\nErreur télémétrie : {e}"
                        
                elif nom_agent == "ULTRON":
                    chemin_fichier = self._extraire_chemin_fichier(texte_entree)
                    if chemin_fichier:
                        try:
                            from app.core.code_reader import lire_code_source
                            contexte_dynamique = f"[CODE SOURCE REÇU]\n{lire_code_source(chemin_fichier)}"
                        except Exception as e:
                            contexte_dynamique = f"[CODE SOURCE REÇU]\nErreur lecture : {e}"
                    else:
                        contexte_dynamique = "[CODE SOURCE REÇU]\nAucun code fourni."

                elif nom_agent == "DAVID":
                    sujet = entree_clean
                    for mot in ["jarvis", "demande à david", "quelles sont", "les dernières", "nouvelles de", "la mise à jour de", "recherche sur", "recherche"]:
                        sujet = sujet.replace(mot, "")
                    sujet = " ".join(re.sub(r"[',\.?!\";:]", " ", sujet).split())
                    
                    annee_actuelle = datetime.now().strftime("%Y")
                    if "cette année" in entree_clean or "dernières" in entree_clean:
                        if annee_actuelle not in sujet:
                            sujet += f" {annee_actuelle}"
                    
                    if not sujet:
                        sujet = f"python programming language updates {annee_actuelle}"

                    resultats_internet = recherche_web(sujet)
                    print(f"\n[DEBUG RAG -> DAVID] Sujet filtré : {sujet}")
                    contexte_dynamique = f"[CONTEXTE INTERNET FOURNI]\n{resultats_internet}"

                elif nom_agent == "VERONICA":
                    flux_emails = recuperer_derniers_emails()
                    contexte_dynamique = "[ALERTE SYSTÈME CRITIQUE]\nAucun e-mail reçu. Flux vide." if not flux_emails or not flux_emails.strip() else f"[E-MAILS RÉELS REÇUS]\n{flux_emails}"
                
                elif nom_agent == "TARS":
                    chemin_cible = "flask_access.log"
                    match = re.search(r'([\w\-/]+\.(?:log|txt))', texte_entree.lower())
                    if match: chemin_cible = match.group(1)
                    contexte_dynamique = f"[FLUX DE LOGS SYSTEME]\n{collecter_logs_systeme(chemin_cible)}"

                elif nom_agent == "GEMINI":
                    url_cible = "https://api.inconnue.com/v1/status"
                    match = re.search(r'(https?://[^\s]+)', texte_entree)
                    if match: url_cible = match.group(1)
                    contexte_dynamique = f"[RETOUR PASSERELLE API]\n{executer_requete_api(url_cible)}"
                    
                else:
                    contexte_dynamique = contexte_memoire
                
                contexte_externe = self.directeur_agents.deleguer_tache(
                    nom_agent, tache=texte_entree, contexte=contexte_dynamique
                )

            # --- PREPARATION DES PROMPTS DE SORTIE ---
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            except Exception:
                maintenant = datetime.now()

            contexte_temporel = f"Information système : Il est actuellement {maintenant.strftime('%A %d %B %Y à %H:%M')}."

            if decision.startswith("AGENT:"):
                # On utilise un rôle Système fort pour forcer JARVIS à n'être qu'un traducteur
                system_prompt_enrichi = (
                    f"{self.system_prompt_base}\n\n"
                    f"{contexte_temporel}\n\n"
                    f"CONSIGNE DE MISSION : Tu viens de recevoir le rapport technique de l'agent {nom_agent}. "
                    "Tu dois UNIQUEMENT reformuler ce rapport pour Monsieur. Si le rapport indique une erreur, "
                    "une absence de connexion ou un échec, transmets cette information de manière brute et transparente. "
                    "N'invente aucune donnée, aucun événement, aucune donnée d'agenda."
                )
                prompt_utilisateur_final = (
                    f"[DONNÉES TECHNIQUES À REFORMULER]\n"
                    f"Rapport de l'agent {nom_agent} : {contexte_externe}\n\n"
                    f"Reste strictement fidèle à ce rapport pour formuler ta réponse à Monsieur."
                )
                messages = [
                    {"role": "system", "content": system_prompt_enrichi},
                    {"role": "user", "content": prompt_utilisateur_final}
                ]
            else:
                system_prompt_enrichi = (
                    f"{self.system_prompt_base}\n\n"
                    f"{contexte_temporel}\n\n"
                    f"[MÉMOIRE INTERNE DES FAITS CONNUS]\n{contexte_memoire}\n"
                    "ATTENTION : Les faits ci-dessus sont des éléments de contexte historiques. Ne t'en sers pas pour inventer "
                    "une actualité ou un rendez-vous fictif si l'utilisateur te dit simplement bonjour ou te pose une question générale."
                )
                prompt_utilisateur_final = texte_entree
                messages = [{"role": "system", "content": system_prompt_enrichi}] + self.historique + [{"role": "user", "content": prompt_utilisateur_final}]

            # --- PARAMÈTRES DE SÉCURITÉ CONTRE L'IMAGINATION (TEMPERATURE & STOP TOKENS) ---
            # Température bloquée à 0.1 partout pour neutraliser les hallucinations narratives
            options_generation = {
                "temperature": 0.1,
                "num_predict": 400,
                "stop": ["Monsieur:", "Mathieu:", "\n\n", "Rapport:"]
            }

            response_stream = await self.client.chat(
                model=self.model,
                messages=messages,
                options=options_generation,
                stream=True
            )

            reponse_complete = []
            async for chunk in response_stream:
                token = chunk["message"]["content"]
                if token:
                    reponse_complete.append(token)
                    yield token

            texte_final = "".join(reponse_complete).strip()
            self.historique.append({"role": "user", "content": texte_entree})
            self.historique.append({"role": "assistant", "content": texte_final})
            if len(self.historique) > 10:
                self.historique = self.historique[-10:]

        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                yield "Monsieur, le cerveau local est inaccessible. Vérifiez le service Ollama."
            else:
                yield f"Monsieur, une anomalie sémantique s'est produite : {str(e)}"