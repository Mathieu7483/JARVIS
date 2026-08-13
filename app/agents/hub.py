#!/usr/bin/env python3
"""
HUB — Routeur central des agents JARVIS.
Délègue chaque tâche à l'agent spécialisé correspondant.
"""
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

class AgentsHub:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self._agents = {}
        self._charger_agents()

    def _charger_agents(self):
        """Charge les agents disponibles de façon lazy (à la demande)."""
        # Les agents sont importés uniquement quand nécessaire
        self._registry = {
            "ULTRON":   "app.agents.ultron",
            "DAVID":    "app.agents.david",
            "MOTHER":   "app.agents.mother",
            "TARS":     "app.agents.tars",
            "VERONICA": "app.agents.veronica",
            "SONNY":    "app.agents.sonny",
            "SKYNET":   "app.agents.skynet",
            "FRIDAY":   "app.agents.friday",
            "GEMINI":   "app.agents.gemini",
        }
        print(f"[HUB] {len(self._registry)} agents enregistrés.")

    def _get_agent(self, nom: str):
        """Charge et retourne l'instance d'un agent (lazy loading)."""
        if nom not in self._agents:
            if nom not in self._registry:
                return None
            try:
                import importlib
                module = importlib.import_module(self._registry[nom])
                # Chaque module expose une classe avec le même nom que l'agent en capitales
                classe = getattr(module, nom.capitalize())
                self._agents[nom] = classe()
                print(f"[HUB] Agent {nom} chargé.")
            except Exception as e:
                print(f"[HUB] Erreur chargement agent {nom} : {e}")
                return None
        return self._agents[nom]

    def deleguer(self, nom_agent: str, tache: str, contexte: str = "") -> str:
        """
        Point d'entrée principal — délègue une tâche à l'agent correspondant.
        Fallback sur le LLM générique si l'agent n'est pas disponible.
        """
        nom_agent = nom_agent.upper().strip()
        print(f"[HUB] Délégation → {nom_agent}")

        agent = self._get_agent(nom_agent)
        if agent:
            try:
                return agent.executer(tache, contexte)
            except Exception as e:
                print(f"[HUB] Erreur agent {nom_agent} : {e}")
                return self._fallback(nom_agent, tache, contexte)
        else:
            print(f"[HUB] Agent {nom_agent} indisponible — fallback LLM")
            return self._fallback(nom_agent, tache, contexte)

    def _fallback(self, nom_agent: str, tache: str, contexte: str = "") -> str:
        """Fallback générique si l'agent est indisponible."""
        try:
            messages = [
                {"role": "system", "content": f"Tu es l'agent {nom_agent} de JARVIS. Réponds en français, sans markdown."},
            ]
            if contexte:
                messages.append({"role": "user", "content": f"Contexte : {contexte}"})
                messages.append({"role": "assistant", "content": "Contexte reçu."})
            messages.append({"role": "user", "content": tache})

            response = self.client.chat(
                model=MODEL,
                messages=messages,
                options={"temperature": 0.3, "num_predict": 400}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[HUB] Erreur critique : {e}"

    def agents_disponibles(self) -> list:
        """Retourne la liste des agents enregistrés."""
        return list(self._registry.keys())