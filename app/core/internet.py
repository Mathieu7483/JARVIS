#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def recherche_web(requete, max_results=3):
    """
    Effectue une recherche sur DuckDuckGo et extrait les résumés des premiers résultats.
    """
    print(f"[JARVIS INTERNET] Recherche en cours pour : '{requete}'...")
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(requete)}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return "Impossible d'accéder au réseau pour le moment."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('a', class_='result__snippet')
        
        snippets = []
        for i, res in enumerate(results[:max_results]):
            snippets.append(f"Source {i+1} : {res.get_text().strip()}")
            
        if not snippets:
            return "Aucun résultat trouvé sur le réseau."
            
        return "\n".join(snippets)
    except Exception as e:
        return f"Erreur lors de la recherche réseau : {e}"