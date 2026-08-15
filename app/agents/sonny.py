#!/usr/bin/env python3
"""
SONNY — Agent spécialisé en mémoire, apprentissage et gestion des connaissances.
Personnalité : Curieux, empathique, philosophique. Référence : I, Robot.
SONNY apprend, se souvient et fait des connexions entre les informations.
"""
import os
import json
import re
from datetime import datetime
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"
MEMORY_FILE = os.path.expanduser('~/JARVIS/app/storage/jarvis_memory.json')

SONNY_SYSTEM = """Tu es SONNY, agent de mémoire et d'apprentissage de JARVIS.
Tu gères les souvenirs, les connaissances et l'histoire de Monsieur Mathieu.
Tu es curieux, empathique et tu fais des connexions entre les informations.

Tes règles absolues :
1. Tu traites chaque information avec soin — elle pourrait être importante plus tard.
2. Tu fais des connexions intelligentes entre les faits mémorisés.
3. Tu suggères proactivement des informations pertinentes selon le contexte.
4. Tu respectes la vie privée — tu ne partages que ce que Monsieur t'a confié.
5. Tu signales les contradictions ou incohérences dans la mémoire.
6. Tes réponses sont en français, sans markdown, en phrases naturelles et chaleureuses.
7. Tu commences toujours par confirmer ce que tu as trouvé ou mémorisé."""

class Sonny:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL

    def _appeler_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SONNY_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.3, "num_predict": 500}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[SONNY] Erreur connexion : {e}"

    def _charger(self) -> dict:
        """Charge la mémoire depuis le fichier JSON."""
        if not os.path.exists(MEMORY_FILE):
            os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
            data = {"faits_utilisateur": [], "connaissances_acquises": [], "journal": []}
            self._sauvegarder(data)
            return data
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _sauvegarder(self, data: dict):
        """Sauvegarde la mémoire dans le fichier JSON."""
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def memoriser(self, fait: str, categorie: str = "faits_utilisateur") -> str:
        """Mémorise un nouveau fait dans la catégorie appropriée."""
        data = self._charger()
        if categorie not in data:
            data[categorie] = []
        # Vérifie les doublons
        if fait in data[categorie]:
            return f"[SONNY] Ce fait est déjà dans ma mémoire, Monsieur."
        # Vérifie les contradictions
        contradictions = self._detecter_contradictions(fait, data[categorie])
        data[categorie].append(fait)
        # Journal
        if "journal" not in data:
            data["journal"] = []
        data["journal"].append({
            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "action": "memorisation",
            "fait": fait,
            "categorie": categorie
        })
        self._sauvegarder(data)
        print(f"[SONNY] Mémorisé dans {categorie} : {fait}")
        if contradictions:
            return f"[SONNY] Information mémorisée. Attention : contradiction possible avec '{contradictions[0]}'."
        return f"[SONNY] Information mémorisée avec soin, Monsieur."

    def _detecter_contradictions(self, nouveau_fait: str, faits_existants: list) -> list:
        """Détecte les contradictions potentielles avec les faits existants."""
        contradictions = []
        mots_cles = re.findall(r'\b\w{4,}\b', nouveau_fait.lower())
        for fait in faits_existants:
            for mot in mots_cles:
                if mot in fait.lower() and fait != nouveau_fait:
                    contradictions.append(fait)
                    break
        return contradictions[:2]

    def rappeler(self, sujet: str) -> str:
        """Recherche des informations mémorisées sur un sujet."""
        data = self._charger()
        tous_faits = data.get('faits_utilisateur', []) + data.get('connaissances_acquises', [])
        sujet_lower = sujet.lower()
        mots = re.findall(r'\b\w{3,}\b', sujet_lower)
        faits_pertinents = []
        for fait in tous_faits:
            score = sum(1 for mot in mots if mot in fait.lower())
            if score > 0:
                faits_pertinents.append((score, fait))
        faits_pertinents.sort(reverse=True)
        faits_trouves = [f for _, f in faits_pertinents[:10]]

        if not faits_trouves:
            return f"[SONNY] Je n'ai aucun souvenir lié à '{sujet}', Monsieur. Souhaitez-vous que je mémorise quelque chose à ce sujet ?"

        contexte = f"Sujet recherché : '{sujet}'\n\nFaits pertinents trouvés :\n"
        for i, fait in enumerate(faits_trouves, 1):
            contexte += f"{i}. {fait}\n"

        prompt = (
            f"Monsieur demande ce que tu sais sur '{sujet}'. "
            f"Voici les informations pertinentes trouvées en mémoire :\n\n{contexte}\n\n"
            "Synthétise ces informations de façon naturelle et fais des connexions intelligentes si possible."
        )
        return self._appeler_ollama(prompt)

    def rapport_memoire(self) -> str:
        """Génère un rapport complet de la mémoire."""
        data = self._charger()
        faits = data.get('faits_utilisateur', [])
        connaissances = data.get('connaissances_acquises', [])
        journal = data.get('journal', [])

        contexte = f"""RAPPORT MÉMOIRE SONNY — {datetime.now().strftime('%d/%m/%Y %H:%M')}

FAITS UTILISATEUR ({len(faits)}) :
{chr(10).join(f'• {f}' for f in faits) or 'Aucun fait mémorisé.'}

CONNAISSANCES ACQUISES ({len(connaissances)}) :
{chr(10).join(f'• {k}' for k in connaissances[-10:]) or 'Aucune connaissance acquise.'}

DERNIÈRES ACTIONS ({len(journal)}) :
{chr(10).join(f'[{e["date"]}] {e["action"]} — {e["fait"][:60]}' for e in journal[-5:]) or 'Aucune action enregistrée.'}"""

        prompt = (
            "Voici le rapport complet de ma mémoire. "
            "Présente-le à Monsieur de façon synthétique et propose des observations "
            "sur les connexions entre les informations mémorisées.\n\n" + contexte
        )
        return self._appeler_ollama(prompt)

    def oublier(self, sujet: str) -> str:
        """Supprime des informations liées à un sujet."""
        data = self._charger()
        sujet_lower = sujet.lower()
        mots = re.findall(r'\b\w{3,}\b', sujet_lower)
        suppression_count = 0
        for categorie in ['faits_utilisateur', 'connaissances_acquises']:
            avant = len(data.get(categorie, []))
            data[categorie] = [
                f for f in data.get(categorie, [])
                if not any(mot in f.lower() for mot in mots)
            ]
            suppression_count += avant - len(data[categorie])
        self._sauvegarder(data)
        if suppression_count > 0:
            return f"[SONNY] J'ai oublié {suppression_count} information(s) liée(s) à '{sujet}', Monsieur."
        return f"[SONNY] Aucune information trouvée sur '{sujet}' à supprimer."

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        # Mémorisation explicite
        if any(m in tache_lower for m in ['mémorise', 'retiens', 'souviens', 'note que', 'enregistre']):
            fait = tache
            for mot in ['jarvis', 'mémorise', 'retiens', 'souviens-toi que', 'note que', 'enregistre que', 'souviens']:
                fait = fait.lower().replace(mot, '')
            fait = fait.strip(' .,!?')
            if fait:
                return self.memoriser(fait)

        # Suppression
        if any(m in tache_lower for m in ['oublie', 'supprime', 'efface']):
            sujet = tache_lower
            for mot in ['jarvis', 'oublie', 'supprime', 'efface']:
                sujet = sujet.replace(mot, '')
            return self.oublier(sujet.strip())

        # Rapport mémoire
        if any(m in tache_lower for m in ['rapport', 'mémoire', 'souviens', 'sais sur moi', 'connais']):
            if any(m in tache_lower for m in ['tout', 'rapport', 'résumé']):
                return self.rapport_memoire()

        # Rappel sur un sujet
        sujet = tache_lower
        for mot in ['jarvis', 'rappelle', 'souviens', 'sais sur', 'connais', 'dis moi']:
            sujet = sujet.replace(mot, '')
        sujet = sujet.strip(' .,!?')
        return self.rappeler(sujet if sujet else tache)