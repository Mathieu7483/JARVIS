import speech_recognition as sr
from config import Config
import os

# Supprime l'affichage des erreurs système dans le terminal
os.environ['ASOUND_LOG_FILE'] = '/dev/null'

class Ears:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True

    def ecouter(self):
        # Utilisation explicite du micro système
        # On ne passe pas d'index, le plugin 'pulse' gérera le lien
        try:
            with sr.Microphone() as source:
                # On laisse un temps de silence pour stabiliser le flux
                self.recognizer.pause_threshold = 0.8
                # On empêche l'ajustement automatique pendant l'écoute
                self.recognizer.dynamic_energy_threshold = False
                print(f"\n[{Config.ASSISTANT_NAME}] : Je vous écoute...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
                print(f"[{Config.ASSISTANT_NAME}] : Analyse...")
                
                texte = self.recognizer.recognize_google(audio, language="fr-FR")
                return texte
            
        except Exception as e:
            # Si l'erreur "No Default Input" persiste, c'est que le service est éteint
            print(f"Erreur ears : {e}")
            return ""