import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.0-pro:generateContent?key={api_key}"

payload = {
    "contents": [{"parts": [{"text": "Réponds uniquement par le mot : OPERATIONNEL"}]}]
}

print(f"Test de l'API en direct...")
try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Succès ! Réponse : {response.json()['candidates'][0]['content']['parts'][0]['text']}")
    else:
        print(f"Erreur HTTP {response.status_code}: {response.text}")
except Exception as e:
    print(f"Erreur de connexion : {e}")