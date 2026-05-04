import os
import asyncio
import edge_tts
import pygame
import time

class Mouth:
    def __init__(self):
        self.voice = "fr-FR-HenriNeural"
        # On initialise pygame une seule fois au début
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

    def parler(self, texte):
        if not texte: return
        
        filename = "temp_voice.mp3"
        communicate = edge_tts.Communicate(texte, self.voice)
        asyncio.run(communicate.save(filename))

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
            pygame.mixer.quit() # <-- INDISPENSABLE pour rendre la main au micro
        except Exception as e:
            print(f"Erreur : {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)