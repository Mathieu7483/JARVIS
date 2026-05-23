#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta

def obtenir_meteo_locale(ville="Thonon-les-Bains"):
    """
    Va chercher les prévisions météo réelles et immédiates via l'API Open-Meteo.
    Retourne une chaîne de caractères formatée pour le Brain de JARVIS.
    """
    try:
        # 1. Obtenir les coordonnées GPS de la ville (Geocoding gratuit)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={ville}&count=1&language=fr&format=json"
        geo_resp = requests.get(geo_url, timeout=5).json()
        
        if not geo_resp.get('results'):
            return f"Désolé Monsieur, je ne trouve pas les coordonnées géographiques pour {ville}."
            
        location = geo_resp['results'][0]
        lat = location['latitude']
        lon = location['longitude']
        nom_complet = location['name']

        # 2. Récupérer la météo (Actuelle + Prévisions)
        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
        meteo_resp = requests.get(meteo_url, timeout=5).json()
        
        # Extraction des données du jour et de demain
        actuelle = meteo_resp['current_weather']
        demain_max = meteo_resp['daily']['temperature_2m_max'][1]
        demain_min = meteo_resp['daily']['temperature_2m_min'][1]
        
        # Interprétation basique du code météo (WMO Code)
        weather_code = meteo_resp['daily']['weathercode'][1]
        conditions = "globalement clémentes"
        if weather_code in [1, 2, 3]: conditions = "partiellement nuageux"
        elif weather_code in [45, 48]: conditions = "brumeux"
        elif weather_code in [51, 53, 55, 61, 63, 65]: conditions = "pluvieux"
        elif weather_code in [71, 73, 75, 85, 86]: conditions = "neigeux"
        elif weather_color := weather_code in [95, 96, 99]: conditions = "orageux"

        infocontext = (
            f"Données réelles pour {nom_complet} :\n"
            f"- Température actuelle : {actuelle['temperature']}°C\n"
            f"- Prévisions pour demain : {conditions}, avec des minimales à {demain_min}°C "
            f"et des maximales atteignant {demain_max}°C."
        )
        return infocontext

    except Exception as e:
        return f"Impossible de joindre les services météo en raison d'une erreur technique : {e}"