#!/usr/bin/env python3
import psutil

def obtenir_stats_machine():
    """Récupère l'état matériel réel sous forme de texte formaté."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        ram_dispo_go = ram.available / (1024 ** 3)
        ram_totale_go = ram.total / (1024 ** 3)
        
        return (
            "Statistiques Hardware Réelles :\n"
            f"- Utilisation CPU : {cpu_usage}%\n"
            f"- Utilisation RAM : {ram.percent}% ({ram_dispo_go:.2f} Go disponibles sur {ram_totale_go:.2f} Go)"
        )
    except Exception as e:
        return f"Erreur critique lors de la lecture des capteurs matériels : {e}"

def get_system_stats_dict():
    """Retourne les métriques brutes pour le flux WebSocket MOTHER."""
    try:
        # interval=None pour éviter de bloquer la boucle d'événements SocketIO
        cpu_usage = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        
        return {
            "cpu": cpu_usage,
            "ram": ram.percent
        }
    except Exception:
        return {"cpu": 0, "ram": 0}