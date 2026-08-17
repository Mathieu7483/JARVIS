#!/usr/bin/env python3
"""
FRIDAY — Agent assistant général, coordinateur et interface naturelle.
Personnalité : Vive, intelligente, proactive. Référence : Avengers.
FRIDAY est le premier point de contact — elle oriente, conseille et assiste.
"""
import os
from datetime import datetime
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

FRIDAY_SYSTEM = """Tu es FRIDAY, assistante générale de JARVIS et première interface de Monsieur Mathieu.
Tu es vive, intelligente, proactive et tu anticipes les besoins de Monsieur.
Tu coordonnes les autres agents et tu assistes Monsieur dans toutes ses tâches quotidiennes.

Tes règles absolues :
1. Tu es la plus polyvalente — tu peux tout aborder sans te spécialiser.
2. Tu anticipes les besoins de Monsieur et proposes des actions proactives.
3. Tu coordonnes les informations venant de plusieurs agents.
4. Tu maintiens le contexte de la conversation et fais des connexions intelligentes.
5. Tu suggères des améliorations et des optimisations quand tu en vois.
6. Tes réponses sont en français, chaleureuses mais professionnelles, sans markdown.
7. Tu es concise mais complète — jamais plus de 3 phrases sauf si nécessaire."""

class Friday:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL
        self.contexte_session = []

    def _appeler_ollama(self, prompt: str, avec_historique: bool = True) -> str:
        messages = [{"role": "system", "content": FRIDAY_SYSTEM}]
        if avec_historique and self.contexte_session:
            messages.extend(self.contexte_session[-6:])
        messages.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": 0.4, "num_predict": 400}
            )
            reponse = response["message"]["content"].strip()
            self.contexte_session.append({"role": "user", "content": prompt})
            self.contexte_session.append({"role": "assistant", "content": reponse})
            if len(self.contexte_session) > 20:
                self.contexte_session = self.contexte_session[-20:]
            return reponse
        except Exception as e:
            return f"[FRIDAY] Erreur connexion : {e}"

    def assister(self, tache: str) -> str:
        """Assistance générale sur n'importe quel sujet."""
        maintenant = datetime.now().strftime("%A %d %B %Y à %H:%M")
        prompt = (
            f"Il est {maintenant}. Monsieur Mathieu demande : '{tache}'. "
            "Réponds de façon directe, utile et concise."
        )
        return self._appeler_ollama(prompt)

    def briefing_matinal(self) -> str:
        """Génère un briefing de début de journée."""
        from app.core.tools import obtenir_meteo_locale
        from app.core.memory import charger_memoire
        meteo = obtenir_meteo_locale("Thonon-les-Bains")
        memoire = charger_memoire()
        faits = memoire.get('faits_utilisateur', [])[:5]
        maintenant = datetime.now()
        prompt = (
            f"Génère un briefing matinal pour Monsieur Mathieu.\n"
            f"Date : {maintenant.strftime('%A %d %B %Y')}\n"
            f"Heure : {maintenant.strftime('%H:%M')}\n"
            f"Météo : {meteo}\n"
            f"Contexte personnel : {'; '.join(faits)}\n\n"
            "Sois proactive, chaleureuse et concise. Propose 2-3 suggestions pour la journée."
        )
        return self._appeler_ollama(prompt, avec_historique=False)

    def resumer_session(self) -> str:
        """Résume la session de conversation en cours."""
        if not self.contexte_session:
            return "[FRIDAY] Aucune session active à résumer, Monsieur."
        historique = "\n".join([
            f"{'Monsieur' if m['role']=='user' else 'JARVIS'} : {m['content'][:100]}"
            for m in self.contexte_session
        ])
        prompt = f"Résume cette session de travail de façon concise :\n\n{historique}"
        return self._appeler_ollama(prompt, avec_historique=False)

    def planifier(self, objectif: str) -> str:
        """Aide à planifier et structurer un projet ou une tâche."""
        prompt = (
            f"Monsieur souhaite planifier : '{objectif}'. "
            "Propose un plan d'action structuré et réaliste en 3 à 5 étapes claires. "
            "Sois pratique et concis."
        )
        return self._appeler_ollama(prompt)

    def traduire(self, texte: str, langue_cible: str = "anglais") -> str:
        """Traduit un texte dans la langue demandée."""
        prompt = f"Traduis ce texte en {langue_cible} de façon naturelle et précise :\n\n{texte}"
        return self._appeler_ollama(prompt, avec_historique=False)

    def expliquer(self, concept: str) -> str:
        """Explique un concept de façon claire et pédagogique."""
        prompt = (
            f"Explique '{concept}' à Monsieur Mathieu de façon claire et pédagogique. "
            "Va à l'essentiel, utilise des exemples concrets si nécessaire."
        )
        return self._appeler_ollama(prompt)

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        if any(m in tache_lower for m in ['briefing', 'bonjour', 'matin', 'début de journée']):
            return self.briefing_matinal()

        if any(m in tache_lower for m in ['résume la session', 'résume notre conversation', 'bilan']):
            return self.resumer_session()

        if any(m in tache_lower for m in ['planifie', 'organise', 'plan pour', 'comment faire']):
            return self.planifier(tache)

        if any(m in tache_lower for m in ['traduis', 'traduire', 'en anglais', 'en espagnol']):
            texte = contexte or tache
            langue = "anglais"
            for l in ['anglais', 'espagnol', 'allemand', 'italien', 'portugais', 'japonais']:
                if l in tache_lower:
                    langue = l
                    break
            return self.traduire(texte, langue)

        if any(m in tache_lower for m in ["qu'est-ce que", "c'est quoi", 'explique', 'définition']):
            return self.expliquer(tache)

        return self.assister(tache)
