import os
import asyncio
import edge_tts
import pygame
import time

class Mouth:
    def __init__(self):
        self.voice = "fr-FR-HenriNeural"

    def parler(self, texte):
        if not texte:
            return

        # Découpe les longues phrases pour éviter le hachage
        chunks = self._decouper(texte)
        filename = "temp_voice.mp3"

        for chunk in chunks:
            if not chunk.strip():
                continue
            try:
                communicate = edge_tts.Communicate(chunk, self.voice)
                asyncio.run(communicate.save(filename))

                pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=8192)
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)

                pygame.mixer.music.unload()
                pygame.mixer.quit()

            except Exception as e:
                print(f"Erreur mouth : {e}")
            finally:
                if os.path.exists(filename):
                    os.remove(filename)

    def _decouper(self, texte, max_chars=200):
        """Découpe le texte en chunks sur les ponctuations naturelles."""
        if len(texte) <= max_chars:
            return [texte]

        chunks = []
        separateurs = ['. ', '! ', '? ', ', ', ' ']

        while len(texte) > max_chars:
            coupe = -1
            for sep in separateurs:
                idx = texte.rfind(sep, 0, max_chars)
                if idx > 0:
                    coupe = idx + len(sep)
                    break
            if coupe == -1:
                coupe = max_chars
            chunks.append(texte[:coupe].strip())
            texte = texte[coupe:].strip()

        if texte:
            chunks.append(texte)

        return chunks