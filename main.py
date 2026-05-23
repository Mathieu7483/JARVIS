#!/usr/bin/env python3
from app.core.processor import Brain
from app.speech.ears import Ears
from app.speech.mouth import Mouth  # Nouvelle importation
from config import Config

def main():
    print(f"--- JARVIS 3.0 : SYSTÈMES COMPLETS ---")
    
    try:
        jarvis_brain = Brain()
        jarvis_ears = Ears()
        jarvis_mouth = Mouth() # Initialisation de la bouche
    except Exception as e:
        print(f"Erreur d'initialisation : {e}")
        return

    jarvis_mouth.parler("Systèmes opérationnels. Je vous écoute, Monsieur.")

    while True:
        try:
            # 1. ÉCOUTER
            vocal_input = jarvis_ears.ecouter()
            
            if not vocal_input:
                continue

            if "quitter" in vocal_input.lower():
                jarvis_mouth.parler("Déconnexion des systèmes. Au revoir, Monsieur.")
                break

            # 2. RÉFLÉCHIR
            reponse = jarvis_brain.reflechir(vocal_input)
            
            # 3. PARLER ET AFFICHER
            print(f"\n[{Config.ASSISTANT_NAME}] : {reponse}")
            jarvis_mouth.parler(reponse)

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()