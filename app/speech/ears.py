import subprocess
from faster_whisper import WhisperModel

# Chemins partagés Windows/WSL
AUDIO_FILE_WSL     = "/mnt/c/Users/mathi/audio_jarvis.wav"
RECORD_SCRIPT = r"C:\Users\mathi\record_audio.py"
PYTHON_WINDOWS = "/mnt/c/Users/mathi/AppData/Local/Programs/Python/Python313/python.exe"

# Mots parasites que Whisper hallucine sur le silence
MOTS_PARASITES = ["amara", "sous-titres", "merci d'avoir", "abonnez"]

class Ears:
    def __init__(self):
        print("[JARVIS] Chargement de Whisper...")
        self.model = WhisperModel("small", device="cpu", compute_type="int8")
        print("[JARVIS] Whisper opérationnel.")

    def ecouter(self):
        """Enregistre via Python Windows puis transcrit avec Whisper."""
        try:
            # Lance l'enregistrement côté Windows
            result = subprocess.run(
                [PYTHON_WINDOWS, RECORD_SCRIPT],
                capture_output=True,
                text=True,
                timeout=20
            )

            if "DONE" not in result.stdout:
                print(f"[JARVIS] Erreur enregistrement : {result.stderr}")
                return ""

            # Transcrit avec Whisper + filtre silence (VAD)
            segments, _ = self.model.transcribe(
                AUDIO_FILE_WSL,
                language="fr",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            texte = " ".join([s.text.strip() for s in segments]).strip()

            # Filtre les hallucinations Whisper sur silence
            if any(p in texte.lower() for p in MOTS_PARASITES):
                return ""

            return texte

        except subprocess.TimeoutExpired:
            print("[JARVIS] Timeout enregistrement.")
            return ""
        except Exception as e:
            print(f"Erreur ears : {e}")
            return ""