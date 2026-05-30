#!/usr/bin/env python3
import subprocess
import os

# ─── PLAYLISTS ───────────────────────────────────────────────────
PLAYLISTS = {
    "jeux":           r"C:\Users\mathi\Music\Playlists\Jeux.wpl",
    "alphabet":       r"C:\Users\mathi\Music\Playlists\Alphabet.wpl",
    "classification": r"C:\Users\mathi\Music\Playlists\Classification.wpl",
    "mathieu":        r"C:\Users\mathi\Music\Playlists\Mathieu.wpl",
    "téléphone":      r"C:\Users\mathi\Music\Playlists\Téléphone.wpl",
    "album":          r"C:\Users\mathi\Music\Playlists\Album.wpl",
}
PLAYLIST_DEFAUT = r"C:\Users\mathi\Music\Playlists\Jeux.wpl"
WMP_EXE = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"

# ─── CATALOGUE DES APPLICATIONS ──────────────────────────────────
APPS = {
    "chrome": {
        "mots": ["chrome", "google", "navigateur", "internet", "web"],
        "lancer": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "fermer": "chrome",
    },
    "discord": {
        "mots": ["discord"],
        "lancer": r"C:\Users\mathi\AppData\Local\Discord\app-1.0.9237\Discord.exe",
        "fermer": "Discord",
    },
    "vscode": {
        "mots": ["vs code", "vscode", "visual studio", "éditeur de code"],
        "lancer": r"C:\Users\mathi\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "fermer": "Code",
    },
    "mediaplayer": {
        "mots": ["windows media player", "media player", "lecteur multimédia", "wmplayer"],
        "lancer": WMP_EXE,
        "fermer": "wmplayer",
    },
    "fusion360": {
        "mots": ["fusion", "fusion 360", "autodesk", "conception", "cao"],
        "lancer": "DYNAMIC_FUSION",
        "fermer": "Fusion360",
    },
    "cura": {
        "mots": ["cura", "ultimaker", "impression 3d", "slicer", "trancheur"],
        "lancer": r"C:\Program Files\UltiMaker Cura 5.11.0\UltiMaker-Cura.exe",
        "fermer": "UltiMaker-Cura",
    },
    "openoffice": {
        "mots": ["openoffice", "open office", "writer", "calc", "tableur", "traitement de texte", "office"],
        "lancer": r"C:\Program Files (x86)\OpenOffice 4\program\soffice.exe",
        "fermer": "soffice",
    },
    "explorateur": {
        "mots": ["explorateur", "explorateur de fichiers", "fichiers", "dossier", "mes documents"],
        "lancer": "EXPLORER",
        "fermer": "explorer",
    },
    "musique": {
        "mots": ["lance la musique", "mets de la musique", "joue de la musique", "musique", "playlist"],
        "lancer": WMP_EXE,
        "fermer": "wmplayer",
    },
}

# ─── COMMANDES SPÉCIALES ─────────────────────────────────────────
COMMANDES_SPECIALES = {
    "volume_haut":  ["augmente le son", "monte le son", "plus fort", "monte le volume", "augmente le volume"],
    "volume_bas":   ["baisse le son", "diminue le son", "moins fort", "baisse le volume", "diminue le volume"],
    "mute":         ["coupe le son", "mute", "silence", "sourdine", "couper le son"],
    "screenshot":   ["capture d'écran", "screenshot", "fais une capture", "prends une capture"],
    "veille":       ["mets en veille", "mode veille", "éteins l'écran", "veille"],
}

MOTS_LANCER = ["lance", "ouvre", "démarre", "start", "ouvrir", "lancer",
               "démarrer", "allume", "exécute", "active", "mets", "joue"]
MOTS_FERMER = ["ferme", "quitte", "arrête", "stop", "fermer", "quitter",
               "arrêter", "éteins", "tue", "close", "kill", "stoppe"]

NOMS_LISIBLES = {
    "chrome":      "Google Chrome",
    "discord":     "Discord",
    "vscode":      "VS Code",
    "mediaplayer": "Windows Media Player",
    "fusion360":   "Fusion 360",
    "cura":        "Cura",
    "openoffice":  "OpenOffice",
    "explorateur": "l'Explorateur de fichiers",
    "musique":     "le lecteur de musique",
}

# ─── EXÉCUTEUR PS1 ───────────────────────────────────────────────
PS1_PATH_WIN = r"C:\Users\mathi\jarvis_cmd.ps1"
PS1_PATH_WSL = "/mnt/c/Users/mathi/jarvis_cmd.ps1"

def run_ps1(script):
    """Écrit un script PS1 et l'exécute via cmd.exe. Retourne toujours True."""
    try:
        with open(PS1_PATH_WSL, 'w', encoding='utf-8') as f:
            f.write(script)
        subprocess.run(
            ["/mnt/c/Windows/System32/cmd.exe", "/c",
             f"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File {PS1_PATH_WIN}"],
            capture_output=True, text=True, timeout=15
        )
    except Exception as e:
        print(f"[ACTIONS] Erreur : {e}")
    return True  # On retourne toujours True — l'app se lance en arrière-plan

# ─── ACTIONS ─────────────────────────────────────────────────────
def lancer_musique(texte):
    t = texte.lower()
    playlist = PLAYLIST_DEFAUT
    nom_playlist = "Jeux"
    for nom, chemin in PLAYLISTS.items():
        if nom in t:
            playlist = chemin
            nom_playlist = nom.capitalize()
            break
    run_ps1(f'Start-Process "{WMP_EXE}" -ArgumentList "/play", "/close", "{playlist}"')
    return f"Je lance la playlist {nom_playlist}, Monsieur."

def lancer_app(app_key):
    # Explorateur de fichiers
    if app_key == "explorateur":
        run_ps1('Start-Process explorer.exe')
        return True

    # Fusion 360 — chemin dynamique (hash change à chaque mise à jour)
    if app_key == "fusion360":
        run_ps1(
            '$basePath = "C:\\Users\\mathi\\AppData\\Local\\Autodesk\\webdeploy\\production"\n'
            '$exe = Get-ChildItem -Path $basePath -Filter "Fusion360.exe" -Recurse '
            '| Sort-Object LastWriteTime -Descending | Select-Object -First 1\n'
            'if ($exe) { Start-Process $exe.FullName }'
        )
        return True

    # Lancement standard
    exe = APPS[app_key]["lancer"]
    run_ps1(f'Start-Process "{exe}"')
    return True

def fermer_app(app_key):
    proc = APPS[app_key]["fermer"]
    succes = run_ps1(f'Stop-Process -Name "{proc}" -Force -ErrorAction SilentlyContinue')
    return succes

def volume_haut():
    run_ps1('$wsh = New-Object -ComObject WScript.Shell\n1..3 | ForEach-Object { $wsh.SendKeys([char]175) }')

def volume_bas():
    run_ps1('$wsh = New-Object -ComObject WScript.Shell\n1..3 | ForEach-Object { $wsh.SendKeys([char]174) }')

def mute():
    run_ps1('$wsh = New-Object -ComObject WScript.Shell\n$wsh.SendKeys([char]173)')

def screenshot():
    run_ps1(r'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(0,0,0,0,$bmp.Size)
$path = "$env:USERPROFILE\Desktop\jarvis_capture_$(Get-Date -Format 'yyyyMMdd_HHmmss').png"
$bmp.Save($path)
''')

def veille():
    run_ps1('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')

# ─── DÉTECTION D'INTENTION ───────────────────────────────────────
def detecter_action(texte):
    t = texte.lower().strip()
    for action, phrases in COMMANDES_SPECIALES.items():
        if any(p in t for p in phrases):
            return (action, None)
    for app_key, app_info in APPS.items():
        if any(mot in t for mot in app_info["mots"]):
            if any(m in t for m in MOTS_FERMER):
                return ("fermer", app_key)
            else:
                return ("lancer", app_key)
    return None

# ─── EXÉCUTEUR PRINCIPAL ─────────────────────────────────────────
def executer_action(texte):
    resultat = detecter_action(texte)
    if not resultat:
        return None

    action, app_key = resultat

    # Commandes spéciales
    if action == "volume_haut":
        volume_haut(); return "Volume augmenté, Monsieur."
    elif action == "volume_bas":
        volume_bas(); return "Volume diminué, Monsieur."
    elif action == "mute":
        mute(); return "Son coupé, Monsieur."
    elif action == "screenshot":
        screenshot(); return "Capture d'écran sauvegardée sur votre bureau, Monsieur."
    elif action == "veille":
        veille(); return "Mise en veille en cours, Monsieur."

    nom = NOMS_LISIBLES.get(app_key, app_key)

    if action == "lancer":
        # Musique → traitement spécial avec playlist
        if app_key in ("musique", "mediaplayer"):
            return lancer_musique(texte)
        # Toutes les autres apps → on lance et on confirme sans vérifier le retour
        lancer_app(app_key)
        return f"Je lance {nom}, Monsieur."

    elif action == "fermer":
        fermer_app(app_key)
        return f"J'ai fermé {nom}, Monsieur."

    return None