#!/usr/bin/env python3
import re
from ollama import Client
from config import Config
from app.actions import executer_action
from app.core.internet import recherche_web
from app.core.email_manager import recuperer_derniers_emails
from app.core.log_analyzer import collecter_logs_systeme
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
        self.model = "llama3.2:3b"
        self.client = Client(host=OLLAMA_HOST)
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

        # Vérification synchrone de la connexion Ollama
        try:
            self.client.chat(
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

    def _evaluer_besoin_outils(self, texte_entree: str) -> str:
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

    def reflechir(self, texte_entree: str):
        """Générateur synchrone — yield token par token pour le streaming."""
        if not texte_entree:
            return

        contexte_externe = ""
        contexte_dynamique = ""
        decision = ""
        entree_clean = texte_entree.lower().strip()

        # --- VOIE ACTIONS (commandes PC) ---
        reponse_action = executer_action(texte_entree)
        if reponse_action:
            yield reponse_action
            return

        # --- VOIE RAPIDE (heure locale) ---
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

            decision = self._evaluer_besoin_outils(entree_clean)

            if decision.startswith("AGENT:"):
                nom_agent = decision.replace("AGENT:", "").strip()
                print(f"[PROCESSING] Délégation à l'agent : {nom_agent}")
                self.historique = []

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
                        sujet = f"actualités IA {annee_actuelle}"
                    resultats_internet = recherche_web(sujet)
                    print(f"[DEBUG RAG -> DAVID] Sujet : {sujet}")
                    contexte_dynamique = f"[CONTEXTE INTERNET FOURNI]\n{resultats_internet}"

                elif nom_agent == "VERONICA":
                    flux_emails = recuperer_derniers_emails()
                    contexte_dynamique = "[ALERTE]\nAucun e-mail reçu." if not flux_emails or not flux_emails.strip() else f"[E-MAILS RÉELS]\n{flux_emails}"

                elif nom_agent == "TARS":
                    chemin_cible = "flask_access.log"
                    match = re.search(r'([\w\-/]+\.(?:log|txt))', texte_entree.lower())
                    if match:
                        chemin_cible = match.group(1)
                    contexte_dynamique = f"[LOGS]\n{collecter_logs_systeme(chemin_cible)}"

                elif nom_agent == "GEMINI":
                    url_cible = "https://api.inconnue.com/v1/status"
                    match = re.search(r'(https?://[^\s]+)', texte_entree)
                    if match:
                        url_cible = match.group(1)
                    contexte_dynamique = f"[RÉPONSE API]\n{self.directeur_agents.interroger_api_externe(url_cible)}"

                elif nom_agent == "WEATHER":
                    from app.core.tools import obtenir_meteo_locale
                    ville = self._extraire_ville(memoire)
                    contexte_dynamique = obtenir_meteo_locale(ville)

                else:
                    contexte_dynamique = contexte_memoire

                contexte_externe = self.directeur_agents.deleguer_tache(
                    nom_agent, tache=texte_entree, contexte=contexte_dynamique
                )

            elif decision == "WEATHER":
                from app.core.tools import obtenir_meteo_locale
                ville = self._extraire_ville(memoire)
                print(f"[JARVIS] Météo pour : {ville}")
                contexte_externe = obtenir_meteo_locale(ville)

            elif decision.startswith("MEMORIZE:"):
                fait = decision.replace("MEMORIZE:", "").strip()
                ajouter_un_fait("faits_utilisateur", fait)
                contexte_externe = "Information mémorisée avec succès."

            # --- CONSTRUCTION DES PROMPTS ---
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            except Exception:
                maintenant = datetime.now()

            contexte_temporel = f"Information système : Il est actuellement {maintenant.strftime('%A %d %B %Y à %H:%M')}."

            if decision.startswith("AGENT:"):
                system_prompt_enrichi = (
                    f"{self.system_prompt_base}\n\n{contexte_temporel}\n\n"
                    f"CONSIGNE : Tu viens de recevoir le rapport de l'agent {nom_agent}. "
                    "Reformule-le pour Monsieur en phrases naturelles. Sois fidèle au rapport."
                )
                prompt_utilisateur_final = (
                    f"Rapport de {nom_agent} : {contexte_externe}\n\n"
                    "Reformule ce rapport pour Monsieur."
                )
                messages = [
                    {"role": "system", "content": system_prompt_enrichi},
                    {"role": "user", "content": prompt_utilisateur_final}
                ]
            else:
                system_prompt_enrichi = (
                    f"{self.system_prompt_base}\n\n{contexte_temporel}\n\n"
                    f"[MÉMOIRE]\n{contexte_memoire}"
                )
                if contexte_externe:
                    system_prompt_enrichi += f"\n\n[DONNÉES EN TEMPS RÉEL]\n{contexte_externe}"
                prompt_utilisateur_final = texte_entree
                messages = [{"role": "system", "content": system_prompt_enrichi}] + self.historique + [{"role": "user", "content": prompt_utilisateur_final}]

            # --- STREAMING SYNCHRONE ---
            options_generation = {
                "temperature": 0.1,
                "num_predict": 400,
                "stop": ["Monsieur:", "Mathieu:", "Rapport:"]
            }

            reponse_complete = []
            for chunk in self.client.chat(
                model=self.model,
                messages=messages,
                options=options_generation,
                stream=True
            ):
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
                yield f"Monsieur, une anomalie s'est produite : {str(e)}"