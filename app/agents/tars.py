#!/usr/bin/env python3
"""
TARS — Agent spécialisé en analyse de logs, diagnostics et détection d'anomalies.
Personnalité : Humour calibré à 75%, pragmatique, analytique. Référence : Interstellar.
"""
import os
import re
from datetime import datetime
from collections import Counter
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

TARS_SYSTEM = """Tu es TARS, agent d'analyse de logs de JARVIS.
Tu es pragmatique, précis et tu as un humour calibré à 75%.
Tu analyses les logs avec une rigueur absolue et tu détectes les anomalies comme un expert sécurité.

Tes règles absolues :
1. Tu identifies les patterns d'erreurs récurrents et leur fréquence.
2. Tu repères les anomalies temporelles (pics d'activité, erreurs groupées).
3. Tu distingues les erreurs critiques des avertissements mineurs.
4. Tu proposes des pistes d'investigation concrètes.
5. Tu estimes la gravité de chaque problème sur une échelle de 1 à 10.
6. Tes réponses sont en français, sans markdown, en phrases naturelles.
7. Tu commences par une conclusion directe avant de détailler."""

# Patterns de détection automatique
PATTERNS_ERREUR = {
    'CRITIQUE': [r'CRITICAL', r'FATAL', r'PANIC', r'EMERGENCY', r'SEGFAULT', r'OOM', r'kernel: \['],
    'ERREUR':   [r'ERROR', r'Exception', r'Traceback', r'Error:', r'FAILED', r'refused'],
    'ALERTE':   [r'WARNING', r'WARN', r'401', r'403', r'500', r'502', r'503'],
    'INFO':     [r'INFO', r'200', r'Started', r'Loaded']
}

class Tars:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL

    def _appeler_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": TARS_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.2, "num_predict": 600}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[TARS] Erreur connexion : {e}"

    def _pre_analyser(self, lignes: list) -> dict:
        """Pré-analyse statistique des logs avant l'envoi à Ollama."""
        stats = {
            'total': len(lignes),
            'critique': 0, 'erreur': 0, 'alerte': 0, 'info': 0,
            'ips': Counter(), 'codes_http': Counter(),
            'heures': Counter(), 'erreurs_frequentes': Counter()
        }

        for ligne in lignes:
            # Classification par niveau
            for niveau, patterns in PATTERNS_ERREUR.items():
                if any(re.search(p, ligne, re.IGNORECASE) for p in patterns):
                    stats[niveau.lower()] += 1
                    break

            # Extraction IPs
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', ligne)
            for ip in ips:
                stats['ips'][ip] += 1

            # Codes HTTP
            codes = re.findall(r'\b[245]\d{2}\b', ligne)
            for code in codes:
                stats['codes_http'][code] += 1

            # Heures d'activité
            heures = re.findall(r'\b(\d{2}):\d{2}:\d{2}\b', ligne)
            for h in heures:
                stats['heures'][h] += 1

            # Messages d'erreur fréquents
            if any(re.search(p, ligne, re.IGNORECASE) for p in PATTERNS_ERREUR['ERREUR']):
                # Nettoie la ligne pour extraire le message principal
                msg = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'IP', ligne)
                msg = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', 'DATETIME', msg)
                msg = msg.strip()[:80]
                stats['erreurs_frequentes'][msg] += 1

        return stats

    def analyser_fichier(self, chemin: str, max_lignes: int = 100) -> str:
        """Analyse un fichier de log complet."""
        chemin_absolu = os.path.abspath(chemin)
        repertoire_racine = os.path.abspath(os.getcwd())

        if not chemin_absolu.startswith(repertoire_racine):
            return "[TARS] Accès refusé : chemin hors du projet."

        if not os.path.exists(chemin_absolu):
            return f"[TARS] Fichier introuvable : {chemin}"

        try:
            with open(chemin_absolu, 'r', encoding='utf-8', errors='replace') as f:
                toutes_lignes = f.readlines()
        except Exception as e:
            return f"[TARS] Erreur de lecture : {e}"

        print(f"[TARS] Analyse de {chemin} ({len(toutes_lignes)} lignes)...")

        # Pré-analyse statistique
        stats = self._pre_analyser(toutes_lignes)

        # Extrait les dernières lignes + les lignes critiques
        dernieres = toutes_lignes[-max_lignes:]
        lignes_critiques = [l for l in toutes_lignes
                           if any(re.search(p, l, re.IGNORECASE)
                                  for p in PATTERNS_ERREUR['CRITIQUE'] + PATTERNS_ERREUR['ERREUR'])][:20]

        # Construction du rapport de pré-analyse
        rapport_stats = f"""FICHIER : {chemin}
VOLUME : {stats['total']} lignes au total
RÉPARTITION : {stats['critique']} critiques | {stats['erreur']} erreurs | {stats['alerte']} alertes | {stats['info']} infos

TOP IPs : {', '.join(f'{ip}({n})' for ip, n in stats['ips'].most_common(5)) or 'Aucune'}
CODES HTTP : {', '.join(f'HTTP{c}({n})' for c, n in stats['codes_http'].most_common(5)) or 'Aucun'}
PICS D'ACTIVITÉ : {', '.join(f'{h}h({n}x)' for h, n in stats['heures'].most_common(3)) or 'Indéterminé'}

ERREURS LES PLUS FRÉQUENTES :
{chr(10).join(f'- ({n}x) {msg}' for msg, n in stats['erreurs_frequentes'].most_common(5)) or 'Aucune'}

DERNIÈRES LIGNES :
{''.join(dernieres[-30:])}

LIGNES CRITIQUES :
{''.join(lignes_critiques) if lignes_critiques else 'Aucune ligne critique détectée.'}"""

        prompt = (
            f"Analyse ce rapport de logs pour Monsieur et donne ton diagnostic :\n\n{rapport_stats}"
        )
        return self._appeler_ollama(prompt)

    def analyser_texte(self, texte_log: str) -> str:
        """Analyse un extrait de log collé directement."""
        lignes = texte_log.split('\n')
        stats = self._pre_analyser(lignes)

        prompt = (
            f"Analyse cet extrait de log ({len(lignes)} lignes, "
            f"{stats['erreur']} erreurs, {stats['critique']} critiques) "
            f"et donne ton diagnostic :\n\n{texte_log[:3000]}"
        )
        return self._appeler_ollama(prompt)

    def surveiller_logs_jarvis(self) -> str:
        """Surveille les logs internes de JARVIS."""
        logs_potentiels = [
            'flask_access.log', 'jarvis.log', 'app.log',
            'logs/jarvis.log', 'logs/access.log'
        ]
        for log in logs_potentiels:
            if os.path.exists(log):
                return self.analyser_fichier(log)

        return "[TARS] Aucun fichier de log JARVIS trouvé. Activité système normale — ou très bonne dissimulation."

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        # Log JARVIS interne
        if any(m in tache_lower for m in ['jarvis', 'propre', 'interne', 'système']):
            if 'log' in tache_lower or 'erreur' in tache_lower:
                return self.surveiller_logs_jarvis()

        # Fichier de log spécifique
        match = re.search(r'([\w\-/\.]+\.(?:log|txt|out|err))', tache)
        if match:
            return self.analyser_fichier(match.group(1))

        # Extrait de log dans le contexte
        if contexte and len(contexte) > 50:
            return self.analyser_texte(contexte)

        # Traceback Python dans la tâche
        if 'Traceback' in tache or 'Error' in tache:
            return self.analyser_texte(tache)

        # Surveillance générale
        return self.surveiller_logs_jarvis()