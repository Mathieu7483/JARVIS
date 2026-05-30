#!/usr/bin/env python3
from ddgs import DDGS

def recherche_web(requete, max_results=3):
    """
    Effectue une recherche via DuckDuckGo et retourne un résumé des résultats.
    """
    print(f"[JARVIS INTERNET] Recherche en cours pour : '{requete}'...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(requete, max_results=max_results))

        if not results:
            return "Aucun résultat trouvé pour cette recherche."

        snippets = []
        for i, r in enumerate(results):
            titre = r.get('title', '').strip()
            corps = r.get('body', '').strip()[:300]
            snippets.append(f"Source {i+1} — {titre} : {corps}")

        return "\n\n".join(snippets)

    except Exception as e:
        return f"Erreur lors de la recherche : {e}"