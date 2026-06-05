#!/usr/bin/env python3
import os

def lire_code_source(chemin_relatif: str) -> str:
    """Lit un fichier de projet pour l'injecter dans le contexte d'Ultron."""
    # Sécurisation du chemin pour rester dans le répertoire JARVIS
    repertoire_racine = os.path.abspath(os.getcwd())
    chemin_absolu = os.path.abspath(os.path.join(repertoire_racine, chemin_relatif))
    
    if not chemin_absolu.startswith(repertoire_racine):
        return "Erreur : Tentative d'accès hors de l'arborescence du projet autorisée."
        
    if not os.path.exists(chemin_absolu):
        return f"Erreur : Le fichier spécifié '{chemin_relatif}' est introuvable."
        
    try:
        with open(chemin_absolu, "r", encoding="utf-8") as f:
            code = f.read()
        return f"--- CONTENU DU FICHIER {chemin_relatif} ---\n{code}\n--- FIN DU FICHIER ---"
    except Exception as e:
        return f"Erreur critique lors de la lecture du code : {str(e)}"