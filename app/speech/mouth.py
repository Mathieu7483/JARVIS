#!/usr/bin/env python3
import os
import asyncio
import edge_tts
import pygame
import time
import threading

class Mouth:
    def __init__(self):
        self.voice = "fr-FR-HenriNeural"
        # Initialisation de la carte son
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=8192)
        
        # Event loop asyncio dédiée à Edge TTS pour éviter la surconsommation de asyncio.run()
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_asyncio_loop, daemon=True)
        self._loop_thread.start()

    def _run_asyncio_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def parler(self, texte_phrase: str):
        """
        Prononce une sous-phrase immédiatement à la volée.
        Méthode non-bloquante pour la restitution texte UI.
        """
        if not texte_phrase or len(texte_phrase.strip()) < 2:
            return

        filename = f"temp_stream_{int(time.time() * 1000)}.mp3"
        self._generer_et_lire(texte_phrase.strip(), filename)

    def consommer_et_parler(self, generateur_tokens):
        """
        Méthode legacy : consomme un générateur de tokens, accumule par phrases
        et lit la parole au fil de l'eau.
        """
        buffer_texte = ""
        declencheurs = ['.', '!', '?', '\n', ';']

        for token in generateur_tokens:
            print(token, end="", flush=True)
            buffer_texte += token

            if any(d in token for d in declencheurs) and len(buffer_texte.strip()) > 10:
                self.parler(buffer_texte.strip())
                buffer_texte = ""

        if buffer_texte.strip():
            self.parler(buffer_texte.strip())

    def _generer_et_lire(self, texte, filename):
        """Génération via Edge-TTS et restitution audio synchrone contrôlée."""
        try:
            async def _async_generate():
                communicate = edge_tts.Communicate(texte, self.voice)
                await communicate.save(filename)

            # Soumission à la boucle asyncio dédiée
            future = asyncio.run_coroutine_threadsafe(_async_generate(), self._loop)
            future.result(timeout=10) # Timeout de sécurité si la connexion Edge déraille

            if os.path.exists(filename):
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    time.sleep(0.02)

                pygame.mixer.music.unload()

        except Exception as e:
            print(f"\n[MOUTH ERROR] : {e}")
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass