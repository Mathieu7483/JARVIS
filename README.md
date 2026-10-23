<p align="center">
  <img src="https://github.com/Mathieu7483/JARVIS/blob/main/assets/Gemini_Generated_Image_suuqetsuuqetsuuq.png" alt="JARVIS HUD Banner" width="600">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Socket.IO-010101?style=for-the-badge&logo=socket.io&logoColor=white" alt="Socket.IO">
  <img src="https://img.shields.io/badge/Ollama-FF6F00?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/Status-En%20cours%20de%20d%C3%A9veloppement-orange?style=for-the-badge" alt="Status">
</p>

# JARVIS — Assistant Personnel Domotique & Écosystème IA Local (v3.0)

**JARVIS** (*Just Rather Very Intelligent System*) est un assistant virtuel personnel conçu pour s'exécuter localement sur un environnement hybride **WSL (Linux) / Windows**. 

Il intègre une interface web HUD immersive en temps réel (**Flask & Socket.IO**), un moteur de traitement basé sur un LLM local (**Ollama / Llama 3.1:8b**), un **écosystème multi-agents spécialisés** ainsi que des capacités d'analyse technique avancées (inspection de code, supervision système, analyse de logs et gestion réseau).

---

## 🧠 Directives Système & Personnalité

Le comportement de JARVIS est régi par des règles strictes définies dans son processeur central :

* **Ton et Posture** : Formel, calme, élégant et strictly professoral. Il s'adresse exclusivement à l'utilisateur en l'appelant **"Monsieur"**.
* **Honnêteté absolue** : Si une erreur de logique ou de programmation est détectée, JARVIS la signale directement et sans détour.
* **Optimisation Vocale** : Les réponses excluent tout formatage Markdown lors des sorties vocales pour garantir une synthèse fluide et naturelle.

---

## 🛠️ Modularité & Architecture Globale

JARVIS repose sur une architecture hautement modulaire permettant de répartir les tâches selon la spécialité requise :

* **Écosystème Multi-Agents (`app/agents/`)** : Routage intelligent des requêtes vers des personnalités/agents spécialisés (*Friday, Tars, Ultron, Skynet, Gemini, Mother, Veronica, David, Sonny, etc.*) via un hub d'orchestration (`agents_hub.py`).
* **Modules d'Analyse Technique (`app/core/`)** :
  * `code_reader.py` : Lecture et analyse syntaxique de code source.
  * `log_analyzer.py` : Inspection et diagnostic des journaux de bord / logs.
  * `system_stats.py` : Télémétrie et métriques matérielles en temps réel.
  * `email_manager.py` & `internet.py` : Interactivité réseau, recherche web et messagerie.
* **Pipeline Vocal (`app/speech/`)** : Captation et transcription STT via **Whisper** (`ears.py`) et synthèse vocale TTS (`mouth.py`).
* **Interaction OS Hôte (`app/actions.py`)** : Pilotage du système hôte Windows depuis WSL via des scripts PowerShell.

---

## 🎨 Interface Utilisateur (HUD 3D)

L'interface web (`templates/index.html`) propose un affichage tête haute (HUD) futuriste alimenté par **Three.js** :

1. **Représentation Neuronale 3D** : Visualisation tridimensionnelle du cerveau synaptique de JARVIS avec rendu additif lumineux (`THREE.AdditiveBlending`).
2. **États Dynamiques via WebSockets** :
   * 🔵 **Cyan (`idle`)** : Mode veille, rotation calme et pulsations régulières.
   * 🟠 **Orange (`thinking`)** : Phase de réflexion du LLM et accélération synaptique.
   * 🟢 **Vert (`speaking`)** : Phase de synthèse vocale ou de réponse.
   * 🟣 **Violet (`keyboard`)** : Mode saisie manuelle.
3. **Double Mode d'Interaction** : Bascule instantanée entre le mode **Vocal** (microphone) et le mode **Clavier** (terminal ou script dédié `main_keyboard.py`).

---

## 📋 Configuration Matérielle & Prérequis

* **GPU cible** : NVIDIA GeForce RTX 3060 (12 Go VRAM recommandés pour charger le modèle quantifié 8B et les composants audio simultanément).
* **Moteur STT** : Faster-Whisper (Medium).
* **Moteur LLM** : Llama 3.1 (8B) hébergé via Ollama sur l'hôte Windows.

### Dépendances Python (`requirements.txt`)

```text
python-dotenv==1.0.1
Flask==3.0.3
Flask-SocketIO==5.3.6
ollama==0.2.1
SpeechRecognition==3.10.4
PyAudio==0.2.14
pyttsx3==2.90
faster-whisper==1.0.3
```

### Liaison Réseau WSL ⇄ Windows

Dans `config.py`, la liaison pointe vers l'adresse IP de la passerelle WSL pour communiquer avec Ollama sur Windows :

```python
OLLAMA_HOST = "http://172.21.176.1:11434"
```

---

## 🚀 Installation & Lancement

1. **Activer le service LLM sur Windows** :
   ```bash
   ollama run llama3.1:8b
   ```

2. **Lancer l'application dans WSL** :
   ```bash
   cd ~/JARVIS
   pip install -r requirements.txt
   python3 app.py
   ```

3. **Accéder à l'interface** :
   Ouvrez votre navigateur web à l'adresse : **`http://localhost:5000`**

*(Note : Pour une interaction exclusivement textuelle sans interface web, vous pouvez exécuter `python3 main_keyboard.py`)*.

---

## ✍️ Auteur

* **Mathieu** — *Élève en programmation, spécialisation Machine Learning* — [Profil GitHub](https://github.com/Mathieu7483)