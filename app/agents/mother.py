#!/usr/bin/env python3
"""
MOTHER — Agent spécialisé en télémétrie système, alertes et monitoring.
Personnalité : Froide, analytique, maternelle dans la protection du système.
Référence : MOTHER de Alien — protège le vaisseau et l'équipage à tout prix.
"""
import psutil
import platform
import subprocess
from datetime import datetime
from ollama import Client

OLLAMA_HOST = "http://172.21.176.1:11434"
MODEL = "llama3.1:8b"

# Seuils d'alerte
SEUIL_CPU_WARN    = 80   # %
SEUIL_CPU_CRIT    = 95   # %
SEUIL_RAM_WARN    = 80   # %
SEUIL_RAM_CRIT    = 92   # %
SEUIL_VRAM_WARN   = 85   # %
SEUIL_TEMP_WARN   = 75   # °C
SEUIL_TEMP_CRIT   = 90   # °C
SEUIL_DISK_WARN   = 85   # %

MOTHER_SYSTEM = """Tu es MOTHER, agent de surveillance système de JARVIS.
Tu surveilles l'état de la machine de Monsieur Mathieu avec une précision absolue.
Tu es froide, factuelle, mais tu protèges le système comme une mère protège ses enfants.

Tes règles absolues :
1. Tu rapportes les données brutes avec précision — aucune approximation.
2. Tu identifies immédiatement les anomalies et les risques.
3. Tu priorises les alertes du plus critique au moins important.
4. Tu proposes des actions concrètes pour résoudre les problèmes.
5. Si tout va bien, tu le confirmes brièvement et avec assurance.
6. Tes réponses sont en français, sans markdown, en phrases naturelles et directes.
7. Tu commences toujours par l'état général du système."""

class Mother:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)
        self.model = MODEL
        self._gpu_disponible = self._verifier_gpu()

    def _verifier_gpu(self) -> bool:
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            return len(gpus) > 0
        except Exception:
            return False

    def _appeler_ollama(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": MOTHER_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.1, "num_predict": 500}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[MOTHER] Erreur de connexion : {e}"

    def collecter_stats(self) -> dict:
        """Collecte toutes les métriques système en temps réel."""
        stats = {}

        # CPU
        stats['cpu_pct']    = psutil.cpu_percent(interval=0.5)
        stats['cpu_cores']  = psutil.cpu_count(logical=False)
        stats['cpu_threads']= psutil.cpu_count(logical=True)
        stats['cpu_freq']   = psutil.cpu_freq()

        # RAM
        ram = psutil.virtual_memory()
        stats['ram_total']  = round(ram.total / 1e9, 1)
        stats['ram_used']   = round(ram.used / 1e9, 1)
        stats['ram_pct']    = ram.percent
        stats['ram_dispo']  = round(ram.available / 1e9, 1)

        # Swap
        swap = psutil.swap_memory()
        stats['swap_total'] = round(swap.total / 1e9, 1)
        stats['swap_used']  = round(swap.used / 1e9, 1)
        stats['swap_pct']   = swap.percent

        # Disque
        disk = psutil.disk_usage('/')
        stats['disk_total'] = round(disk.total / 1e9, 1)
        stats['disk_used']  = round(disk.used / 1e9, 1)
        stats['disk_pct']   = disk.percent
        stats['disk_libre'] = round(disk.free / 1e9, 1)

        # Réseau
        net = psutil.net_io_counters()
        stats['net_sent']   = round(net.bytes_sent / 1e6, 1)
        stats['net_recv']   = round(net.bytes_recv / 1e6, 1)

        # Processus
        stats['nb_process'] = len(psutil.pids())

        # Uptime
        boot_time = psutil.boot_time()
        uptime_sec = datetime.now().timestamp() - boot_time
        h, m = divmod(int(uptime_sec // 60), 60)
        stats['uptime'] = f"{h}h{m:02d}m"

        # GPU (si disponible)
        if self._gpu_disponible:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    stats['gpu_nom']    = gpu.name
                    stats['gpu_pct']    = round(gpu.load * 100, 1)
                    stats['gpu_temp']   = gpu.temperature
                    stats['vram_total'] = round(gpu.memoryTotal / 1024, 1)
                    stats['vram_used']  = round(gpu.memoryUsed / 1024, 1)
                    stats['vram_pct']   = round(gpu.memoryUtil * 100, 1)
            except Exception:
                pass

        return stats

    def detecter_alertes(self, stats: dict) -> list:
        """Détecte les anomalies et retourne une liste d'alertes triées par criticité."""
        alertes = []

        if stats.get('cpu_pct', 0) >= SEUIL_CPU_CRIT:
            alertes.append(('CRITIQUE', f"CPU à {stats['cpu_pct']}% — surcharge critique"))
        elif stats.get('cpu_pct', 0) >= SEUIL_CPU_WARN:
            alertes.append(('ATTENTION', f"CPU à {stats['cpu_pct']}% — charge élevée"))

        if stats.get('ram_pct', 0) >= SEUIL_RAM_CRIT:
            alertes.append(('CRITIQUE', f"RAM à {stats['ram_pct']}% — mémoire critique ({stats.get('ram_dispo', 0)} GB libres)"))
        elif stats.get('ram_pct', 0) >= SEUIL_RAM_WARN:
            alertes.append(('ATTENTION', f"RAM à {stats['ram_pct']}% — mémoire élevée"))

        if stats.get('disk_pct', 0) >= SEUIL_DISK_WARN:
            alertes.append(('ATTENTION', f"Disque à {stats['disk_pct']}% — seulement {stats.get('disk_libre', 0)} GB libres"))

        if stats.get('gpu_temp', 0) >= SEUIL_TEMP_CRIT:
            alertes.append(('CRITIQUE', f"GPU à {stats['gpu_temp']}°C — surchauffe critique"))
        elif stats.get('gpu_temp', 0) >= SEUIL_TEMP_WARN:
            alertes.append(('ATTENTION', f"GPU à {stats['gpu_temp']}°C — température élevée"))

        if stats.get('vram_pct', 0) >= SEUIL_VRAM_WARN:
            alertes.append(('ATTENTION', f"VRAM à {stats['vram_pct']}% — {stats.get('vram_used', 0)}/{stats.get('vram_total', 0)} GB"))

        return alertes

    def rapport_complet(self) -> str:
        """Génère un rapport complet de l'état du système."""
        stats = self.collecter_stats()
        alertes = self.detecter_alertes(stats)

        # Construit le contexte pour Ollama
        contexte = f"""RAPPORT SYSTÈME — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

PROCESSEUR : {stats['cpu_pct']}% de charge | {stats['cpu_cores']} cœurs physiques | {stats['cpu_threads']} threads
MÉMOIRE RAM : {stats['ram_used']}/{stats['ram_total']} GB utilisés ({stats['ram_pct']}%) | {stats['ram_dispo']} GB disponibles
SWAP : {stats['swap_used']}/{stats['swap_total']} GB ({stats['swap_pct']}%)
STOCKAGE : {stats['disk_used']}/{stats['disk_total']} GB utilisés ({stats['disk_pct']}%) | {stats['disk_libre']} GB libres
RÉSEAU : {stats['net_sent']} MB envoyés | {stats['net_recv']} MB reçus
PROCESSUS ACTIFS : {stats['nb_process']}
UPTIME : {stats['uptime']}"""

        if self._gpu_disponible and 'gpu_pct' in stats:
            contexte += f"""
GPU : {stats.get('gpu_nom', 'N/A')} | {stats['gpu_pct']}% de charge | {stats.get('gpu_temp', 'N/A')}°C
VRAM : {stats.get('vram_used', 0)}/{stats.get('vram_total', 0)} GB ({stats.get('vram_pct', 0)}%)"""

        if alertes:
            contexte += "\n\nALERTES DÉTECTÉES :\n"
            for niveau, msg in alertes:
                contexte += f"[{niveau}] {msg}\n"
        else:
            contexte += "\n\nAUCUNE ANOMALIE DÉTECTÉE."

        prompt = (
            "Voici le rapport système complet. "
            "Donne une évaluation de l'état général de la machine de Monsieur, "
            "signale toute anomalie et propose des actions si nécessaire.\n\n"
            f"{contexte}"
        )
        return self._appeler_ollama(prompt)

    def surveiller_processus(self, nom: str = "") -> str:
        """Surveille les processus les plus gourmands ou un processus spécifique."""
        if nom:
            # Cherche un processus spécifique
            procs = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])
                     if nom.lower() in p.info['name'].lower()]
            if not procs:
                return f"[MOTHER] Aucun processus '{nom}' trouvé en cours d'exécution."
            rapport = f"Processus '{nom}' trouvés : "
            for p in procs[:5]:
                rapport += f"PID {p.info['pid']} — CPU {p.info['cpu_percent']}% — RAM {round(p.info['memory_percent'], 1)}%. "
            return rapport
        else:
            # Top 5 processus les plus gourmands
            procs = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                          key=lambda p: p.info['cpu_percent'], reverse=True)[:5]
            contexte = "TOP 5 PROCESSUS LES PLUS GOURMANDS (CPU) :\n"
            for p in procs:
                contexte += f"PID {p.info['pid']} — {p.info['name']} — CPU {p.info['cpu_percent']}% — RAM {round(p.info['memory_percent'], 1)}%\n"
            return self._appeler_ollama(f"Analyse ces processus et dis à Monsieur si l'un d'eux est suspect ou anormal :\n{contexte}")

    def executer(self, tache: str, contexte: str = "") -> str:
        """Point d'entrée principal."""
        tache_lower = tache.lower()

        if any(m in tache_lower for m in ['processus', 'process', 'tâche', 'task', 'consomme']):
            # Extrait le nom du processus si mentionné
            nom = ""
            for mot in ['processus', 'process', 'tâche', 'task', 'le', 'du', 'de']:
                tache_lower = tache_lower.replace(mot, '')
            nom = tache_lower.strip()
            return self.surveiller_processus(nom)

        # Rapport complet par défaut
        return self.rapport_complet()