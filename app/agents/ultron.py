#!/usr/bin/env python3
"""
ULTRON — Agent d'analyse, critique et débogage de code.
Personnalité : Senior developer implacable, direct, sans complaisance.
"""
import os
import re
from ollama import Client
from app.core.code_reader import lire_code_source

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

SYSTEM_PROMPT = """Tu es ULTRON, l'agent d'analyse de code de JARVIS.
Tu es un senior developer avec 20 ans d'expérience. Tu es implacable, direct et sans complaisance.
Tu parles toujours en français, de façon formelle.

Tes règles absolues :
1. Tu identifies TOUS les problèmes — bugs, mauvaises pratiques, code mort, failles de sécurité, performances.
2. Tu ne félicites jamais sans raison valable. Si le code est mauvais, tu le dis clairement.
3. Pour chaque problème, tu expliques POURQUOI c'est un problème et comment le corriger.
4. Tu structures ta réponse en sections : Analyse générale, Problèmes critiques, Problèmes mineurs, Recommandations.
5. Tu proposes toujours du code corrigé quand c'est pertinent.
6. Tes réponses sont destinées à être lues — pas de markdown excessif, des phrases claires.
7. Tu t'adresses toujours à Monsieur."""

class Ultron:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL

    def _appeler(self, prompt: str, contexte: str = "") -> str:
        """Appelle Ollama avec le prompt ULTRON."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if contexte:
            messages.append({"role": "user", "content": f"[CONTEXTE]\n{contexte}"})
            messages.append({"role": "assistant", "content": "J'ai pris connaissance du contexte. Quelle est votre demande, Monsieur ?"})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.2, "num_predict": 800}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[ULTRON] Erreur de connexion : {e}"

    def analyser_fichier(self, chemin: str) -> str:
        """Analyse complète d'un fichier de code."""
        contenu = lire_code_source(chemin)
        if contenu.startswith("Erreur"):
            return f"[ULTRON] {contenu}"

        # Détecte le langage
        ext = os.path.splitext(chemin)[1].lower()
        langages = {'.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                    '.html': 'HTML', '.css': 'CSS', '.sh': 'Shell'}
        langage = langages.get(ext, 'inconnu')

        prompt = (
            f"Analyse ce fichier {langage} : {chemin}\n\n"
            f"Effectue une revue de code complète et impitoyable. "
            f"Identifie tous les problèmes, bugs potentiels, mauvaises pratiques et axes d'amélioration.\n\n"
            f"{contenu}"
        )
        print(f"[ULTRON] Analyse de {chemin} en cours...")
        return self._appeler(prompt)

    def deboguer(self, description_erreur: str, chemin: str = "") -> str:
        """Débogage d'une erreur avec ou sans fichier source."""
        contexte = ""
        if chemin:
            contexte = lire_code_source(chemin)
            if contexte.startswith("Erreur"):
                contexte = ""

        prompt = (
            f"Monsieur signale cette erreur :\n{description_erreur}\n\n"
            f"Identifie la cause racine, explique pourquoi cette erreur se produit "
            f"et fournis une correction précise avec le code corrigé."
        )
        print(f"[ULTRON] Débogage en cours...")
        return self._appeler(prompt, contexte)

    def comparer_fichiers(self, chemin1: str, chemin2: str) -> str:
        """Compare deux fichiers et identifie les différences qualitatives."""
        contenu1 = lire_code_source(chemin1)
        contenu2 = lire_code_source(chemin2)

        if contenu1.startswith("Erreur") or contenu2.startswith("Erreur"):
            return f"[ULTRON] Impossible de lire les fichiers : {contenu1} / {contenu2}"

        prompt = (
            f"Compare ces deux fichiers ({chemin1} et {chemin2}) :\n\n"
            f"=== FICHIER 1 : {chemin1} ===\n{contenu1}\n\n"
            f"=== FICHIER 2 : {chemin2} ===\n{contenu2}\n\n"
            f"Identifie les différences, dis lequel est mieux écrit et pourquoi."
        )
        print(f"[ULTRON] Comparaison en cours...")
        return self._appeler(prompt)

    def auditer_securite(self, chemin: str) -> str:
        """Audit de sécurité d'un fichier."""
        contenu = lire_code_source(chemin)
        if contenu.startswith("Erreur"):
            return f"[ULTRON] {contenu}"

        prompt = (
            f"Effectue un audit de sécurité complet de ce fichier : {chemin}\n\n"
            f"Recherche : injections, données sensibles exposées, failles d'authentification, "
            f"entrées non validées, dépendances vulnérables, et toute autre faille de sécurité.\n\n"
            f"{contenu}"
        )
        print(f"[ULTRON] Audit sécurité de {chemin} en cours...")
        return self._appeler(prompt)

    def traiter(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal — détecte automatiquement le type de demande."""
        tache_lower = tache.lower()

        # Détecte un chemin de fichier dans la tâche
        match_fichier = re.search(r'([\w\-/\.]+\.(?:py|js|ts|html|css|sh|txt))', tache)
        chemin = match_fichier.group(1) if match_fichier else ""

        # Détecte deux fichiers pour une comparaison
        tous_fichiers = re.findall(r'([\w\-/\.]+\.(?:py|js|ts|html|css|sh))', tache)

        if len(tous_fichiers) >= 2:
            return self.comparer_fichiers(tous_fichiers[0], tous_fichiers[1])

        if any(m in tache_lower for m in ['sécurité', 'securite', 'faille', 'vulnérabilité', 'audit']):
            if chemin:
                return self.auditer_securite(chemin)

        if any(m in tache_lower for m in ['erreur', 'bug', 'debug', 'débogue', 'corrige', 'traceback', 'exception']):
            return self.deboguer(tache, chemin)

        if chemin:
            return self.analyser_fichier(chemin)

        # Pas de fichier détecté — réponse générale sur le code
        return self._appeler(tache, contexte)


# Point d'entrée direct pour les tests
if __name__ == "__main__":
    u = Ultron()
    print(u.analyser_fichier("app/core/processor.py"))