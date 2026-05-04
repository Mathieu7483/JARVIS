import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time

class VoiceEngine:
    def __init__(self):
        pygame.mixer.init()
        self.language = 'fr'

    def dire(self, texte):
        print(f"JARVIS: {texte}")
        try:
            tts = gTTS(text=texte, lang=self.language, slow=False)
            filename = "temp_voice.mp3"
            tts.save(filename)
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
            os.remove(filename)
        except Exception as e:
            print(f"Erreur audio : {e}")

    def ecouter(self):
        recognizer = sr.Recognizer()
        with sr.Microphone(device_index=27) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(">>> En attente d'ordres...")
            try:
                audio = recognizer.listen(source, timeout=5)
                return recognizer.recognize_google(audio, language="fr-FR").lower()
            except:
                return ""