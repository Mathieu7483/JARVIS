#!/usr/bin/env python3
# app/core/api_connector.py
import requests

def executer_requete_api(url: str, methode: str = "GET", payload: dict = None, headers: dict = None) -> str:
    """
    Effectue un appel HTTP structuré pour le compte de GEMINI.
    """
    print(f"[JARVIS PROTOCOL] GEMINI initie une requête {methode} vers : '{url}'...")
    
    # Sécurité temporaire : Si l'URL n'est pas configurée ou est une simulation
    if "api.inconnue.com" in url:
        return "ERREUR_GATEWAY : Jeton d'authentification manquant ou URL non routée."
        
    try:
        if methode.upper() == "GET":
            reponse = requests.get(url, headers=headers, timeout=5)
        elif methode.upper() == "POST":
            reponse = requests.post(url, json=payload, headers=headers, timeout=5)
        else:
            return f"ERREUR_METHODE : Méthode {methode} non supportée."
            
        return f"STATUT : {reponse.status_code}\nBODY : {reponse.text}"
        
    except Exception as e:
        return f"ERREUR_CONNEXION : Échec de la liaison avec l'API. Détails : {str(e)}"