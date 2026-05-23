#!/usr/bin/env python3
import json
import os

MEMORY_FILE = os.path.expanduser('~/JARVIS/app/storage/jarvis_memory.json')

def charger_memoire():
    if not os.path.exists(MEMORY_FILE):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        # Faits initiaux de base
        initial_data = {
            "faits_utilisateur": [
                "L'utilisateur s'appelle Monsieur Mathieu.",
                "Monsieur étudie le Machine Learning et la programmation."
            ],
            "connaissances_acquises": []
        }
        sauvegarder_memoire(initial_data)
        return initial_data
        
    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def sauvegarder_memoire(data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ajouter_un_fait(categorie, fait):
    data = charger_memoire()
    if fait not in data[categorie]:
        data[categorie].append(fait)
        sauvegarder_memoire(data)
        print(f"[JARVIS MEMORY] Nouveau fait enregistré dans {categorie} : {fait}")