#!/usr/bin/env python3
"""
GEMINI — Agent spécialisé en connexions API et services externes.
Personnalité : Connecteur universel, précis, technique. Référence : Jumeaux numériques.
GEMINI fait le pont entre JARVIS et le monde des services externes.
"""
import os
import re
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

GEMINI_SYSTEM = """Tu es GEMINI, agent de connexion aux services externes de JARVIS.
Tu interroges les APIs, services cloud et domotique pour Monsieur Mathieu.
Tu es précis, technique et tu présentes les données de façon claire.

Tes règles absolues :
1. Tu rapportes les données brutes de façon structurée et lisible.
2. Tu signales immédiatement les erreurs de connexion avec leur cause.
3. Tu interprètes les données techniques en langage naturel.
4. Tu proposes des actions basées sur les données reçues.
5. Tu ne stockes jamais les clés API dans les réponses.
6. Tes réponses sont en français, sans markdown, en phrases naturelles.
7. Tu commences par confirmer la source des données."""

# APIs configurées via .env
APIS_DISPONIBLES = {
    'openweather': {
        'url': 'https://api.openweathermap.org/data/2.5/weather',
        'cle': os.getenv('OPENWEATHER_KEY', ''),
        'description': 'Météo détaillée OpenWeatherMap'
    },
    'newsapi': {
        'url': 'https://newsapi.org/v2/top-headlines',
        'cle': os.getenv('NEWSAPI_KEY', ''),
        'description': 'Actualités en temps réel'
    },
    'github': {
        'url': 'https://api.github.com',
        'cle': os.getenv('GITHUB_TOKEN', ''),
        'description': 'GitHub API — repos, issues, PRs'
    },
}

class Gemini:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'JARVIS/3.0'})

    def _appeler_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": GEMINI_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.2, "num_predict": 400}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[GEMINI] Erreur connexion Ollama : {e}"

    def requete_generique(self, url: str, params: dict = None,
                          headers: dict = None, methode: str = "GET") -> str:
        """Effectue une requête HTTP générique."""
        try:
            print(f"[GEMINI] Requête {methode} → {url}")
            if methode == "GET":
                resp = self.session.get(url, params=params, headers=headers, timeout=8)
            elif methode == "POST":
                resp = self.session.post(url, json=params, headers=headers, timeout=8)
            else:
                return f"[GEMINI] Méthode {methode} non supportée."

            resp.raise_for_status()
            try:
                data = resp.json()
                data_str = json.dumps(data, ensure_ascii=False, indent=2)[:2000]
            except Exception:
                data_str = resp.text[:2000]

            prompt = (
                f"Voici la réponse de l'API {url} :\n\n{data_str}\n\n"
                "Interprète ces données pour Monsieur de façon claire et utile."
            )
            return self._appeler_ollama(prompt)

        except requests.exceptions.ConnectionError:
            return f"[GEMINI] Impossible de joindre {url} — vérifiez la connexion réseau."
        except requests.exceptions.Timeout:
            return f"[GEMINI] Timeout — {url} ne répond pas."
        except requests.exceptions.HTTPError as e:
            return f"[GEMINI] Erreur HTTP {e.response.status_code} : {e}"
        except Exception as e:
            return f"[GEMINI] Erreur inattendue : {e}"

    def meteo_openweather(self, ville: str = "Thonon-les-Bains") -> str:
        """Météo détaillée via OpenWeatherMap."""
        cle = APIS_DISPONIBLES['openweather']['cle']
        if not cle:
            return "[GEMINI] Clé OpenWeatherMap manquante dans le fichier .env (OPENWEATHER_KEY)"
        params = {'q': ville, 'appid': cle, 'units': 'metric', 'lang': 'fr'}
        return self.requete_generique(APIS_DISPONIBLES['openweather']['url'], params=params)

    def actualites(self, sujet: str = "", pays: str = "fr") -> str:
        """Actualités via NewsAPI."""
        cle = APIS_DISPONIBLES['newsapi']['cle']
        if not cle:
            return "[GEMINI] Clé NewsAPI manquante dans le fichier .env (NEWSAPI_KEY)"
        params = {'country': pays, 'apiKey': cle, 'pageSize': 5}
        if sujet:
            params['q'] = sujet
        return self.requete_generique(APIS_DISPONIBLES['newsapi']['url'], params=params)

    def github_repos(self, utilisateur: str = "") -> str:
        """Infos GitHub — repos publics d'un utilisateur."""
        if not utilisateur:
            utilisateur = os.getenv('GITHUB_USERNAME', 'Mathieu7483')
        url = f"https://api.github.com/users/{utilisateur}/repos"
        headers = {}
        token = APIS_DISPONIBLES['github']['cle']
        if token:
            headers['Authorization'] = f"token {token}"
        params = {'sort': 'updated', 'per_page': 5}
        return self.requete_generique(url, params=params, headers=headers)

    def tester_api(self, url: str) -> str:
        """Teste si une API est accessible et retourne son statut."""
        try:
            resp = self.session.get(url, timeout=5)
            return (
                f"API {url} accessible. "
                f"Statut HTTP {resp.status_code}. "
                f"Temps de réponse : {resp.elapsed.total_seconds():.2f}s."
            )
        except Exception as e:
            return f"API {url} inaccessible : {e}"

    def lister_apis(self) -> str:
        """Liste les APIs disponibles et leur état."""
        rapport = "APIs configurées dans JARVIS :\n\n"
        for nom, config in APIS_DISPONIBLES.items():
            cle_presente = "✓ Clé configurée" if config['cle'] else "✗ Clé manquante"
            rapport += f"{nom.upper()} — {config['description']} — {cle_presente}\n"
        return self._appeler_ollama(f"Présente à Monsieur l'état des APIs disponibles :\n\n{rapport}")

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        # Liste des APIs
        if any(m in tache_lower for m in ['liste', 'disponibles', 'quelles apis', 'apis']):
            return self.lister_apis()

        # Météo OpenWeather
        if any(m in tache_lower for m in ['openweather', 'météo détaillée']):
            ville = "Thonon-les-Bains"
            match = re.search(r'à ([A-Z][a-zéèêëàâùûü\-]+(?:\s[A-Z][a-z]+)*)', tache)
            if match:
                ville = match.group(1)
            return self.meteo_openweather(ville)

        # Actualités
        if any(m in tache_lower for m in ['actualités', 'news', 'nouvelles']):
            sujet = ""
            for mot in ['actualités sur', 'news sur', 'nouvelles sur']:
                if mot in tache_lower:
                    sujet = tache_lower.split(mot)[-1].strip()
            return self.actualites(sujet)

        # GitHub
        if any(m in tache_lower for m in ['github', 'repos', 'dépôts']):
            utilisateur = ""
            match = re.search(r'github\s+(\w+)', tache_lower)
            if match:
                utilisateur = match.group(1)
            return self.github_repos(utilisateur)

        # Test d'une URL
        url_match = re.search(r'https?://[^\s]+', tache)
        if url_match:
            if any(m in tache_lower for m in ['teste', 'vérifie', 'ping', 'accessible']):
                return self.tester_api(url_match.group(0))
            return self.requete_generique(url_match.group(0))

        # Requête générique
        return self._appeler_ollama(
            f"Monsieur demande : '{tache}'. "
            "Explique-lui ce que tu peux faire comme connexion API pour l'aider."
        )
