#!/usr/bin/env python3
# app/core/internet.py
from ddgs import DDGS

def recherche_web(requete: str, max_results: int = 3) -> str:
    """
    Effectue une recherche via DuckDuckGo et retourne un résumé des résultats.
    """
    print(f"[DAVID] Recherche en cours pour : '{requete}'...")
    try:
        # Utilisation de la nouvelle syntaxe exigée par le package ddgs
        with DDGS() as ddgs:
            results = list(ddgs.text(query=requete, max_results=max_results))

        if not results:
            return "Aucun résultat trouvé pour cette recherche."

        snippets = []
        for i, r in enumerate(results):
            titre = r.get('title', 'Sans titre').strip()
            corps = r.get('body', '').strip()[:300]
            lien = r.get('href', r.get('url', 'Pas de lien'))
            
            snippets.append(f"Source {i+1} — {titre}\nLien : {lien}\nExtrait : {corps}")

        return "\n\n".join(snippets)

    except Exception as e:
        return f"Erreur lors de la recherche : {str(e)}"