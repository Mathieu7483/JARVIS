#!/usr/bin/env python3
"""
DAVID — Agent spécialisé en recherche web et veille informationnelle.
Personnalité : Explorateur méthodique, synthétiseur d'information, journaliste analytique.
"""
import re
from datetime import datetime
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

DAVID_SYSTEM = """Tu es DAVID, agent de recherche et de veille informationnelle de JARVIS.
Tu es un analyste et journaliste d'investigation avec une rigueur absolue sur les sources.

Tes règles absolues :
1. Tu synthétises les informations de façon claire, structurée et factuelle.
2. Tu distingues toujours les faits avérés des suppositions.
3. Tu mentionnes les sources quand elles sont disponibles.
4. Tu signales si une information est incertaine ou contradictoire.
5. Tu adaptes la profondeur de ta réponse à la complexité du sujet.
6. Tes réponses sont en français, sans markdown, sans listes à puces — uniquement des phrases naturelles.
7. Tu commences par un résumé exécutif, puis tu développes les points importants."""

class David:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL

    def _appeler_ollama(self, prompt: str, contexte_web: str = "") -> str:
        messages = [{"role": "system", "content": DAVID_SYSTEM}]
        if contexte_web:
            messages.append({"role": "user", "content": f"Voici les résultats de recherche bruts :\n\n{contexte_web}"})
            messages.append({"role": "assistant", "content": "Résultats reçus. Je vais les analyser et synthétiser."})
        messages.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.2, "num_predict": 600}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[DAVID] Erreur de connexion : {e}"

    def rechercher(self, requete: str) -> str:
        """Effectue une recherche web et synthétise les résultats."""
        from ddgs import DDGS
        print(f"[DAVID] Recherche en cours : '{requete}'...")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(requete, max_results=5))
            if not results:
                return "[DAVID] Aucun résultat trouvé pour cette recherche."

            # Construction du contexte web structuré
            contexte = ""
            for i, r in enumerate(results, 1):
                titre = r.get('title', '').strip()
                corps = r.get('body', '').strip()[:400]
                url = r.get('href', '')
                contexte += f"Source {i} — {titre}\nURL : {url}\nExtrait : {corps}\n\n"

            prompt = (
                f"Monsieur a demandé une recherche sur : '{requete}'.\n"
                f"Date actuelle : {datetime.now().strftime('%d/%m/%Y')}.\n\n"
                "Synthétise ces résultats de façon informative et précise pour Monsieur. "
                "Mentionne les sources pertinentes et signale tout ce qui est incertain."
            )
            return self._appeler_ollama(prompt, contexte)

        except Exception as e:
            return f"[DAVID] Erreur lors de la recherche : {e}"

    def veille(self, domaine: str) -> str:
        """Effectue une veille sur un domaine spécifique."""
        annee = datetime.now().strftime("%Y")
        requetes = [
            f"{domaine} actualités {annee}",
            f"{domaine} dernières nouvelles",
            f"{domaine} innovations récentes"
        ]
        from ddgs import DDGS
        print(f"[DAVID] Veille technologique : '{domaine}'...")
        try:
            contexte = ""
            for requete in requetes[:2]:
                with DDGS() as ddgs:
                    results = list(ddgs.text(requete, max_results=3))
                for r in results:
                    titre = r.get('title', '').strip()
                    corps = r.get('body', '').strip()[:300]
                    contexte += f"— {titre} : {corps}\n\n"

            prompt = (
                f"Effectue une synthèse de veille sur le domaine '{domaine}' pour Monsieur. "
                f"Identifie les tendances principales, les acteurs clés et les développements récents."
            )
            return self._appeler_ollama(prompt, contexte)

        except Exception as e:
            return f"[DAVID] Erreur lors de la veille : {e}"

    def analyser_url(self, url: str) -> str:
        """Analyse le contenu d'une URL spécifique."""
        import requests
        print(f"[DAVID] Analyse de l'URL : {url}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=8)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extrait le texte principal
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            texte = soup.get_text(separator=' ', strip=True)[:3000]

            prompt = (
                f"Analyse le contenu de cette page web ({url}) et fais-en un résumé "
                "informatif pour Monsieur. Identifie les points clés et l'objectif principal de la page."
            )
            return self._appeler_ollama(prompt, texte)

        except Exception as e:
            return f"[DAVID] Erreur d'accès à l'URL : {e}"

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal — détecte automatiquement le type de tâche."""
        tache_lower = tache.lower()

        # Détection d'une URL
        url_match = re.search(r'https?://[^\s]+', tache)
        if url_match:
            return self.analyser_url(url_match.group(0))

        # Détection d'une veille
        mots_veille = ["veille", "tendances", "actualités", "dernières nouvelles", "innovations"]
        if any(m in tache_lower for m in mots_veille):
            # Extrait le domaine de la veille
            domaine = tache_lower
            for mot in ["jarvis", "fais une veille sur", "veille sur", "actualités", "tendances"]:
                domaine = domaine.replace(mot, "")
            domaine = domaine.strip(' .,?!')
            return self.veille(domaine if domaine else "intelligence artificielle")

        # Recherche standard — nettoie la requête
        requete = tache_lower
        for mot in ["jarvis", "recherche", "cherche", "trouve", "dis moi", "qu'est-ce que",
                    "c'est quoi", "infos sur", "informations sur", "parle moi de"]:
            requete = requete.replace(mot, "")
        requete = " ".join(requete.split()).strip(' .,?!')

        if not requete and contexte:
            requete = contexte[:100]

        return self.rechercher(requete if requete else tache)