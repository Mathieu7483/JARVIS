import os
import asyncio
import edge_tts
import pygame
import time

class Mouth:
    def __init__(self):
        self.voice = "fr-FR-HenriNeural"
        # Initialisation stable et pérenne de la carte son
        pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=8192)

    def consommer_et_parler(self, generateur_tokens):
        """
        Prend en entrée le générateur synchrone du Brain, accumule les mots 
        par phrases complètes et les prononce à la volée.
        """
        buffer_texte = ""
        filename = "temp_stream_voice.mp3"
        
        # Ponctuations qui marquent une fin de phrase nette pour HenriNeural
        declencheurs_phrase = ['.', '!', '?', '\n']

        for token in generateur_tokens:
            print(token, end="", flush=True) # Affiche la réponse dans la console en temps réel
            buffer_texte += token

            # Si on détecte une fin de phrase et qu'elle contient assez de matière
            if any(d in token for d in declencheurs_phrase) and len(buffer_texte.strip()) > 10:
                phrase_a_dire = buffer_texte.strip()
                buffer_texte = "" # On vide le buffer pour la phrase suivante
                
                self._generer_et_lire(phrase_a_dire, filename)

        # Une fois le générateur vidé, s'il reste des mots dans le buffer (ex: pas de point final)
        if buffer_texte.strip():
            self._generer_et_lire(buffer_texte.strip(), filename)

    def _generer_et_lire(self, texte, filename):
        """Sous-méthode interne d'exécution audio, encapsulant l'appel asynchrone de edge_tts."""
        try:
            # Encapsulation stricte de la partie asynchrone pour edge_tts
            async def generer_audio():
                communicate = edge_tts.Communicate(texte, self.voice)
                await communicate.save(filename)
                
            # Exécution isolée de la coroutine
            asyncio.run(generer_audio())

            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.05) # Attente synchrone standard

            pygame.mixer.music.unload()
        except Exception as e:
            print(f"\n[MOUTH ERROR] : {e}")
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass