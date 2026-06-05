#!/usr/bin/env python3
import psutil

def obtenir_stats_machine():
    """Récupère l'état matériel réel de la machine hôte."""
    try:
        # Mesure de la charge CPU globale sur un intervalle court
        cpu_usage = psutil.cpu_percent(interval=0.5)
        
        # Récupération des constantes de la mémoire vive
        ram = psutil.virtual_memory()
        ram_dispo_go = ram.available / (1024 ** 3)
        ram_totale_go = ram.total / (1024 ** 3)
        
        # Structuration du rapport brut destiné à MOTHER
        return (
            "Statistiques Hardware Réelles :\n"
            f"- Utilisation CPU : {cpu_usage}%\n"
            f"- Utilisation RAM : {ram.percent}% ({ram_dispo_go:.2f} Go disponibles sur {ram_totale_go:.2f} Go)"
        )
    except Exception as e:
        return f"Erreur critique lors de la lecture des capteurs matériels : {e}"
