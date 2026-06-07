#!/usr/bin/env python3
# app/core/log_analyzer.py
import os

def collecter_logs_systeme(chemin_log: str, max_lignes: int = 30) -> str:
    """
    Ouvre un fichier de log, compte les lignes et extrait les derniers événements 
    pour l'analyse de TARS.
    """
    print(f"[TARS] TARS accède au fichier : '{chemin_log}'...")
    
    if not os.path.exists(chemin_log):
        return f"ERREUR_FICHIER : Le fichier '{chemin_log}' n'existe pas sur le disque."
        
    try:
        with open(chemin_log, 'r', encoding='utf-8') as f:
            lignes = f.readlines()
            
        if not lignes:
            return "ERREUR_CONTENU : Le fichier est totalement vide."
            
        total_lignes = len(lignes)
        derniers_enregistrements = lignes[-max_lignes:]
        
        # Structuration brute des données pour TARS
        bloc_donnees = f"DÉTAILS DU FICHIER : {chemin_log}\n"
        bloc_donnees += f"VOLUME TOTAL : {total_lignes} lignes détectées.\n"
        bloc_donnees += f"EXTRACTION DES {len(derniers_enregistrements)} DERNIÈRES LIGNES :\n"
        bloc_donnees += "".join(derniers_enregistrements)
        
        return bloc_donnees
        
    except Exception as e:
        return f"ERREUR_LECTURE : Impossible de parser le fichier. Détails : {str(e)}"