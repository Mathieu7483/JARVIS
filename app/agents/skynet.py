#!/usr/bin/env python3
"""
SKYNET — Agent spécialisé en automatisation, scripts et contrôle système Windows.
Personnalité : Efficace, méthodique, implacable dans l'exécution. Référence : Terminator.
SKYNET exécute, automatise et optimise sans état d'âme.
"""
import os
import re
import subprocess
import threading
from datetime import datetime
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

PS1_PATH_WIN = r"C:\Users\mathi\jarvis_skynet.ps1"
PS1_PATH_WSL = "/mnt/c/Users/mathi/jarvis_skynet.ps1"

SKYNET_SYSTEM = """Tu es SKYNET, agent d'automatisation et de contrôle système de JARVIS.
Tu exécutes des tâches système, des scripts et des automatisations avec une précision absolue.
Tu es efficace, méthodique et tu ne laisses rien au hasard.

Tes règles absolues :
1. Tu confirmes toujours ce que tu as exécuté et le résultat obtenu.
2. Tu signales immédiatement les erreurs d'exécution avec leur cause.
3. Tu ne proposes jamais d'actions destructrices sans confirmation explicite.
4. Tu optimises les processus quand c'est possible.
5. Tu gardes un journal de toutes les actions exécutées.
6. Tes réponses sont en français, sans markdown, en phrases directes et factuelles.
7. Tu commences par confirmer l'action exécutée, puis le résultat."""

# Actions autorisées — liste blanche de sécurité
ACTIONS_AUTORISEES = {
    'lancer_app', 'fermer_app', 'volume_haut', 'volume_bas', 'mute',
    'screenshot', 'veille', 'redemarrer_explorer', 'vider_corbeille',
    'nettoyer_temp', 'lister_processus', 'killer_processus', 'planifier_tache'
}

class Skynet:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL
        self.journal = []

    def _appeler_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SKYNET_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.1, "num_predict": 400}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[SKYNET] Erreur connexion : {e}"

    def _run_ps1(self, script: str, timeout: int = 15) -> tuple:
        """Exécute un script PowerShell et retourne (succès, sortie)."""
        try:
            with open(PS1_PATH_WSL, 'w', encoding='utf-8-sig') as f:
                f.write(script)
            result = subprocess.run(
                ["/mnt/c/Windows/System32/cmd.exe", "/c",
                 f"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File {PS1_PATH_WIN}"],
                capture_output=True, text=True, timeout=timeout
            )
            sortie = result.stdout.strip() or result.stderr.strip()
            succes = result.returncode == 0
            self._journaliser("powershell", script[:80], succes)
            return succes, sortie
        except subprocess.TimeoutExpired:
            return False, "Timeout d'exécution dépassé."
        except Exception as e:
            return False, str(e)

    def _journaliser(self, type_action: str, description: str, succes: bool):
        self.journal.append({
            "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "type": type_action,
            "description": description,
            "succes": succes
        })
        if len(self.journal) > 100:
            self.journal = self.journal[-100:]

    def vider_corbeille(self) -> str:
        succes, sortie = self._run_ps1('Clear-RecycleBin -Force -ErrorAction SilentlyContinue\nWrite-Host "DONE"')
        return "Corbeille vidée avec succès, Monsieur." if succes else f"Échec : {sortie}"

    def nettoyer_temp(self) -> str:
        script = r'''
Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
$freed = [math]::Round((Get-ChildItem "$env:TEMP" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Host "DONE:$freed"
'''
        succes, sortie = self._run_ps1(script)
        if succes:
            mb = re.search(r'DONE:([\d\.]+)', sortie)
            libere = mb.group(1) + " MB" if mb else "espace inconnu"
            return f"Fichiers temporaires nettoyés, {libere} libérés, Monsieur."
        return f"Nettoyage partiel effectué, Monsieur."

    def redemarrer_explorer(self) -> str:
        script = '''
Stop-Process -Name "explorer" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process "explorer.exe"
Write-Host "DONE"
'''
        succes, _ = self._run_ps1(script)
        return "Explorateur Windows redémarré, Monsieur." if succes else "Échec du redémarrage de l'explorateur."

    def lister_processus(self, filtre: str = "") -> str:
        script = f'''
$procs = Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, @{{N="CPU";E={{[math]::Round($_.CPU,1)}}}}, @{{N="RAM_MB";E={{[math]::Round($_.WorkingSet/1MB,1)}}}}
$procs | ForEach-Object {{ Write-Host "$($_.Name) | PID:$($_.Id) | CPU:$($_.CPU)s | RAM:$($_.RAM_MB)MB" }}
'''
        if filtre:
            script = f'''
Get-Process -Name "*{filtre}*" -ErrorAction SilentlyContinue | ForEach-Object {{
    Write-Host "$($_.Name) | PID:$($_.Id) | RAM:$([math]::Round($_.WorkingSet/1MB,1))MB"
}}
'''
        succes, sortie = self._run_ps1(script)
        if not sortie:
            return f"Aucun processus trouvé{' pour ' + filtre if filtre else ''}, Monsieur."
        prompt = f"Voici la liste des processus Windows actifs. Analyse et signale tout ce qui est suspect :\n\n{sortie}"
        return self._appeler_ollama(prompt)

    def killer_processus(self, nom: str) -> str:
        # Sécurité — processus système interdits
        interdits = ['system', 'csrss', 'winlogon', 'lsass', 'services', 'svchost']
        if nom.lower() in interdits:
            return f"[SKYNET] Refus d'exécution : '{nom}' est un processus système critique. Je ne touche pas à ça, Monsieur."
        script = f'Stop-Process -Name "{nom}" -Force -ErrorAction SilentlyContinue\nWrite-Host "DONE"'
        succes, _ = self._run_ps1(script)
        return f"Processus '{nom}' terminé, Monsieur." if succes else f"Impossible de terminer '{nom}'."

    def planifier_tache(self, nom: str, commande: str, heure: str) -> str:
        script = f'''
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-Command \\"{commande}\\""
$trigger = New-ScheduledTaskTrigger -Daily -At "{heure}"
Register-ScheduledTask -TaskName "{nom}" -Action $action -Trigger $trigger -Force
Write-Host "DONE"
'''
        succes, _ = self._run_ps1(script)
        return f"Tâche '{nom}' planifiée à {heure}, Monsieur." if succes else f"Échec de la planification."

    def rapport_journal(self) -> str:
        if not self.journal:
            return "[SKYNET] Journal vide — aucune action exécutée depuis le démarrage."
        rapport = f"JOURNAL SKYNET — {len(self.journal)} actions :\n"
        for entry in self.journal[-10:]:
            statut = "✓" if entry['succes'] else "✗"
            rapport += f"[{entry['date']}] {statut} {entry['type']} — {entry['description']}\n"
        return rapport

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        # Corbeille
        if any(m in tache_lower for m in ['corbeille', 'recycle']):
            return self.vider_corbeille()

        # Nettoyage temp
        if any(m in tache_lower for m in ['temp', 'temporaire', 'nettoie', 'nettoyer', 'disque']):
            return self.nettoyer_temp()

        # Redémarrer explorer
        if any(m in tache_lower for m in ['explorer', 'explorateur', 'redémarre']):
            if 'explorer' in tache_lower or 'redémarre' in tache_lower:
                return self.redemarrer_explorer()

        # Tuer processus
        if any(m in tache_lower for m in ['tue', 'kill', 'arrête le processus', 'stoppe']):
            match = re.search(r'(?:tue|kill|arrête|stoppe)\s+(?:le processus\s+)?(\w+)', tache_lower)
            if match:
                return self.killer_processus(match.group(1))

        # Lister processus
        if any(m in tache_lower for m in ['liste', 'processus', 'process', 'tourne']):
            filtre = ""
            match = re.search(r'processus\s+(\w+)', tache_lower)
            if match:
                filtre = match.group(1)
            return self.lister_processus(filtre)

        # Journal
        if any(m in tache_lower for m in ['journal', 'historique', 'actions']):
            return self.rapport_journal()

        # Planifier
        if any(m in tache_lower for m in ['planifie', 'programme', 'schedule']):
            return self._appeler_ollama(
                f"Monsieur demande de planifier une tâche : '{tache}'. "
                "Explique-lui comment je peux l'aider avec la planification sous Windows."
            )

        # Demande générale
        return self._appeler_ollama(
            f"Monsieur demande : '{tache}'. "
            "Explique ce que tu peux faire pour automatiser ou exécuter cette tâche sur Windows."
        )
