#!/usr/bin/env python3
from ollama import Client
from config import Config
from app.actions import executer_action
from app.core.internet import recherche_web
from app.core.tools import obtenir_meteo_locale
from app.core.memory import charger_memoire, ajouter_un_fait
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

    def _evaluer_besoin_outils(self, texte_entree):
        """
        Première passe d'analyse pour déterminer si JARVIS doit interagir avec le monde extérieur.
        """
        system_analyse = (
            "Tu es le module de classification d'intentions de JARVIS. Analyse la demande de l'utilisateur "
            "et réponds STRICTEMENT avec l'un de ces mots-clés standardisés, sans aucune autre fioriture ni ponctuation :\n"
            "- Si l'utilisateur demande le temps qu'il fait, la météo ou les températures d'une ville : 'WEATHER'\n"
            "- Si la demande nécessite une recherche internet, une actualité ou une information récente : 'SEARCH: <sujet de recherche>'\n"
            "- Si l'utilisateur te donne une information personnelle sur lui à mémoriser pour l'avenir : 'MEMORIZE: <le fait résumé>'\n"
            "- Sinon (salutations, code informatique, discussion générale) : 'NONE'"
        )
        try:
            res = self.client.generate(
                model=self.model,
                system=system_analyse,
                prompt=texte_entree,
                options={"temperature": 0.0}  # Température nulle pour une classification fiable
            )
            return res['response'].strip()
        except Exception:
            return "NONE"

    def reflechir(self, texte_entree):
        if not texte_entree:
            return ""

        entree_clean = texte_entree.lower().strip()

        # --- VOIE ACTIONS (commandes PC) ---
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

        # --- VOIE INTELLIGENTE ET CONNECTÉE (OLLAMA + TOOLS) ---
        try:
            # 1. Extraction de la mémoire persistante
            memoire = charger_memoire()
            contexte_memoire = "Faits connus concernant Monsieur :\n" + "\n".join(memoire['faits_utilisateur'])
            if memoire['connaissances_acquises']:
                contexte_memoire += "\n\nDernières connaissances acquises sur le web :\n" + "\n".join(memoire['connaissances_acquises'][-3:])

            # 2. Analyse de l'intention et exécution des outils
            decision = self._evaluer_besoin_outils(texte_entree)
            contexte_externe = ""

            if decision == "WEATHER":
                contexte_externe = obtenir_meteo_locale(texte_entree)
            elif decision.startswith("SEARCH:"):
                sujet = decision.replace("SEARCH:", "").strip()
                contexte_externe = recherche_web(sujet)
                ajouter_un_fait("connaissances_acquises", f"Recherche sur {sujet} effectuée le {datetime.now().strftime('%d/%m')}.")
            elif decision.startswith("MEMORIZE:"):
                fait = decision.replace("MEMORIZE:", "").strip()
                ajouter_un_fait("faits_utilisateur", fait)
                contexte_externe = "Système de mémoire mis à jour. L'information a été consignée dans vos archives."

            # 3. Construction des invites temporelles et contextuelles
            try:
                maintenant = datetime.now(ZoneInfo("Europe/Paris"))
            except Exception:
                maintenant = datetime.now()
            
            horodatage = maintenant.strftime("%A %d %B %Y à %H:%M")
            contexte_temporel = f"Information système : Il est actuellement {horodatage}."

            # Construction du prompt système enrichi pour la session de chat
            system_prompt_enrichi = (
                f"{self.system_prompt_base}\n\n"
                f"{contexte_temporel}\n\n"
                f"[MÉMOIRE INTERNE]\n{contexte_memoire}"
            )

            if contexte_externe:
                system_prompt_enrichi += f"\n\n[DONNÉES DU WEB ET OUTILS EN TEMPS RÉEL]\n{contexte_externe}"

            # 4. Envoi de la structure de discussion complète à Ollama
            messages = [
                {"role": "system", "content": system_prompt_enrichi}
            ] + self.historique + [
                {"role": "user", "content": texte_entree}
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.6, "num_predict": 250}
            )

            reponse_texte = response["message"]["content"].strip()

            # 5. Sauvegarde de l'échange dans l'historique de la session en cours
            self.historique.append({"role": "user", "content": texte_entree})
            self.historique.append({"role": "assistant", "content": reponse_texte})
            if len(self.historique) > 20:
                self.historique = self.historique[-20:]

            return reponse_texte

        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                return "Monsieur, le cerveau local est inaccessible. Vérifiez qu'Ollama est bien lancé sur Windows."
            return f"Monsieur, une erreur est survenue lors de l'analyse de votre requête : {str(e)}"