#!/usr/bin/env python3
import requests

class WeatherTool:
    """
    Outil météo professionnel pour l'infrastructure JARVIS.
    Permet au LLM d'extraire des données réelles pour n'importe quelle ville.
    """
    
    def __init__(self):
        self.geo_base_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_base_url = "https://api.open-meteo.com/v1/forecast"

    def _get_coordinates(self, ville: str) -> dict:
        """Méthode interne pour obtenir la latitude et la longitude."""
        params = {"name": ville, "count": 1, "language": "fr", "format": "json"}
        response = requests.get(self.geo_base_url, params=params, timeout=5).json()
        
        if not response.get('results'):
            return {}
        return response['results'][0]

    def _interpret_wmo_code(self, code: int) -> str:
        """Traduit le code WMO Open-Meteo en description claire."""
        if code in [0]: return "ciel dégagé"
        if code in [1, 2, 3]: return "partiellement nuageux"
        if code in [45, 48]: return "brumeux"
        if code in [51, 53, 55, 61, 63, 65]: return "pluvieux"
        if code in [71, 73, 75, 85, 86]: return "neigeux"
        if code in [95, 96, 99]: return "orageux"
        return "globalement clément"

    def execute(self, ville: str = "Thonon-les-Bains") -> dict:
        """
        Exécute l'appel API et retourne un dictionnaire de données brutes.
        """
        try:
            # 1. Récupération des coordonnées GPS
            location = self._get_coordinates(ville)
            if not location:
                return {"error": f"Impossible de localiser la ville : {ville}"}
            
            lat = location['latitude']
            lon = location['longitude']
            nom_complet = location['name']

            # 2. Récupération de la météo
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": "auto"
            }
            meteo_resp = requests.get(self.weather_base_url, params=params, timeout=5).json()
            
            # 3. Extraction et structuration des données propres
            actuelle = meteo_resp['current_weather']
            weather_code = meteo_resp['daily']['weathercode'][1]
            
            # On retourne un dictionnaire propre pour le LLM
            return {
                "ville": nom_complet,
                "temperature_actuelle": actuelle['temperature'],
                "vitesse_vent": actuelle['windspeed'],
                "previsions_demain": {
                    "condition": self._interpret_wmo_code(weather_code),
                    "temp_min": meteo_resp['daily']['temperature_2m_min'][1],
                    "temp_max": meteo_resp['daily']['temperature_2m_max'][1]
                }
            }

        except Exception as e:
            return {"error": f"Erreur technique lors de la récupération météo : {str(e)}"}
