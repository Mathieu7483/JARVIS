import subprocess
import os

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
        "lancer": r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe",
        "fermer": "wmplayer",
    },
    "fusion360": {
        "mots": ["fusion", "fusion 360", "autodesk", "conception", "cao"],
        "lancer": r"C:\Users\mathi\AppData\Local\Autodesk\webdeploy\production\4826aec956713f599d57385857ff62484fd50dd3\Fusion360.exe",
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
        "lancer": r"explorer.exe",
        "fermer": "explorer",
    },
    "musique": {
        "mots": ["lance la musique", "mets de la musique", "joue de la musique", "musique"],
        "lancer": r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe",
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

# ─── MOTS DÉCLENCHEURS ───────────────────────────────────────────
MOTS_LANCER = ["lance", "ouvre", "démarre", "start", "ouvrir", "lancer",
               "démarrer", "allume", "exécute", "active", "mets"]
MOTS_FERMER = ["ferme", "quitte", "arrête", "stop", "fermer", "quitter",
               "arrêter", "éteins", "tue", "close", "kill", "stoppe"]

def powershell(cmd):
    """Exécute une commande PowerShell depuis WSL."""
    try:
        result = subprocess.run(
            ["/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
             "-NonInteractive", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[ACTIONS] Erreur PowerShell : {e}")
        return False

def lancer_app(app_key):
    exe = APPS[app_key]["lancer"]
    return powershell(f'Start-Process "{exe}"')

def fermer_app(app_key):
    proc = APPS[app_key]["fermer"]
    return powershell(f'Stop-Process -Name "{proc}" -Force -ErrorAction SilentlyContinue')

def volume_haut():
    return powershell('''
        $wsh = New-Object -ComObject WScript.Shell
        1..3 | ForEach-Object { $wsh.SendKeys([char]175) }
    ''')

def volume_bas():
    return powershell('''
        $wsh = New-Object -ComObject WScript.Shell
        1..3 | ForEach-Object { $wsh.SendKeys([char]174) }
    ''')

def mute():
    return powershell('''
        $wsh = New-Object -ComObject WScript.Shell
        $wsh.SendKeys([char]173)
    ''')

def screenshot():
    return powershell('''
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.Screen] | Out-Null
        $bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        $g.CopyFromScreen(0,0,0,0,$bmp.Size)
        $path = "$env:USERPROFILE\Desktop\jarvis_capture_$(Get-Date -Format 'yyyyMMdd_HHmmss').png"
        $bmp.Save($path)
        Write-Host $path
    ''')

def veille():
    return powershell('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')

# ─── DÉTECTION D'INTENTION ───────────────────────────────────────
def detecter_action(texte):
    t = texte.lower().strip()

    # Commandes spéciales en priorité
    for action, phrases in COMMANDES_SPECIALES.items():
        if any(p in t for p in phrases):
            return (action, None)

    # Détection app + action
    for app_key, app_info in APPS.items():
        if any(mot in t for mot in app_info["mots"]):
            if any(m in t for m in MOTS_FERMER):
                return ("fermer", app_key)
            else:
                return ("lancer", app_key)

    return None

# ─── NOM LISIBLE ─────────────────────────────────────────────────
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

# ─── EXÉCUTEUR PRINCIPAL ─────────────────────────────────────────
def executer_action(texte):
    resultat = detecter_action(texte)
    if not resultat:
        return None

    action, app_key = resultat

    if action == "volume_haut":
        volume_haut()
        return "Volume augmenté, Monsieur."
    elif action == "volume_bas":
        volume_bas()
        return "Volume diminué, Monsieur."
    elif action == "mute":
        mute()
        return "Son coupé, Monsieur."
    elif action == "screenshot":
        screenshot()
        return "Capture d'écran sauvegardée sur votre bureau, Monsieur."
    elif action == "veille":
        veille()
        return "Mise en veille en cours, Monsieur."

    nom = NOMS_LISIBLES.get(app_key, app_key)

    if action == "lancer":
        succes = lancer_app(app_key)
        if succes:
            return f"Je lance {nom}, Monsieur."
        else:
            return f"Je n'ai pas pu lancer {nom}, Monsieur. Le chemin d'installation est peut-être différent."
    elif action == "fermer":
        succes = fermer_app(app_key)
        if succes:
            return f"J'ai fermé {nom}, Monsieur."
        else:
            return f"Je n'ai pas pu fermer {nom}, Monsieur."

    return None