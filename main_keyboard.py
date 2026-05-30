#!/usr/bin/env python3
"""
JARVIS — Mode clavier (silencieux)
Idéal pour une utilisation nocturne sans micro ni haut-parleurs.
"""
from app.core.processor import Brain
from config import Config

def main():
    print(f"--- JARVIS 3.0 : MODE CLAVIER ---")
    print(f"Tapez votre message et appuyez sur Entrée.")
    print(f"Tapez 'quitter' pour arrêter.\n")

    try:
        jarvis_brain = Brain()
    except Exception as e:
        print(f"Erreur d'initialisation : {e}")
        return

    while True:
        try:
            texte = input(f"[VOUS] → ").strip()

            if not texte:
                continue

            if texte.lower() in ["quitter", "exit", "quit"]:
                print(f"[{Config.ASSISTANT_NAME}] Au revoir, Monsieur.")
                break

            reponse = jarvis_brain.reflechir(texte)
            print(f"\n[{Config.ASSISTANT_NAME}] {reponse}\n")

        except KeyboardInterrupt:
            print(f"\n[{Config.ASSISTANT_NAME}] Au revoir, Monsieur.")
            break

if __name__ == "__main__":
    main()