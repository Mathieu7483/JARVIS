# 📚 Documentation Technique — JARVIS v3.0

Ce document constitue la documentation de référence pour le déploiement, l'utilisation et la maintenance de **JARVIS**.

## 📄 Table des Matières

1. [Vue d'Ensemble & Philosophie](#1-vue-densemble--philosophie)

2. [Installation & Déploiement](#2-installation--déploiement)

3. [Guide de Configuration](#3-guide-de-configuration)

4. [Écosystème Multi-Agents](#4-écosystème-multi-agents)

5. [Modules d'Analyse & Outillage](#5-modules-danalyse--outillage)

6. [Modes d'Interaction (Web & CLI)](#6-modes-dinteraction-web--cli)

7. [Résolution de Problèmes (Troubleshooting)](#7-résolution-de-problèmes-troubleshooting)

## 1. Vue d'Ensemble & Philosophie

**JARVIS** est un assistant domotique et technique conçu pour fonctionner en **totale autonomie locale**. Il s'exécute dans un environnement hybride où le traitement logique principal et les scripts réseau tournent sous **WSL (Linux)**, tandis que l'inférence lourde du modèle de langage (**Ollama / Llama 3.1:8b**) et l'exécution d'actions système s'appuient sur l'hôte **Windows**.

## 2. Installation & Déploiement

### Prérequis Matériels & Logiciels

* **OS** : Windows 10/11 avec WSL2 (Ubuntu / Debian recommandé).

* **GPU** : Carte NVIDIA avec au moins 8 à 12 Go VRAM (ex: RTX 3060).

* **LLM Engine** : [Ollama](https://ollama.com/) installé sur Windows.

* **Python** : Version 3.10 ou supérieure sous WSL.

### Étapes d'Installation

1. **Préparation du service LLM (Côté Windows)** :
   Ouvrez un terminal Windows et téléchargez / lancez le modèle :

   ```
   ollama run llama3.1:8b
   
   ```

2. **Configuration de l'environnement WSL** :
   Dans votre terminal WSL, clonez le dépôt et installez les dépendances :

   ```
   git clone https://github.com/Mathieu7483/JARVIS.git
   cd JARVIS
   pip install -r requirements.txt
   
   ```

3. **Lancement du serveur central** :

   ```
   python3 app.py
   
   ```

## 3. Guide de Configuration

La configuration du système est centralisée dans le fichier `config.py` :

```
# IP de la passerelle WSL vers l'hôte Windows pour Ollama
OLLAMA_HOST = "http://172.21.176.1:11434"

# Modèle par défaut
MODEL_NAME = "llama3.1:8b"

# Configuration du serveur web
HOST = "0.0.0.0"
PORT = 5000
DEBUG = False  # Maintenir impérativement à False pour éviter les doublons de threads

```

## 4. Écosystème Multi-Agents

JARVIS repose sur une architecture multi-agents coordonnée par `app/core/agents_hub.py`. Lorsqu'une requête est soumise, le hub détermine quel agent spécialisé est le plus qualifié pour y répondre :

| Agent (`app/agents/`) | Rôle & Spécialité | 
| ----- | ----- | 
| **`friday.py`** | Gestion de l'agenda, tâches quotidiennes et rappels. | 
| **`tars.py`** | Assistance scientifique, logique formelle et mathématiques. | 
| **`ultron.py`** | Analyse de sécurité, audits et opérations système poussées. | 
| **`skynet.py`** | Surveillance réseau et contrôle des périphériques domotiques. | 
| **`gemini.py` / `hub.py`** | Traitement des requêtes généralistes et synthèse d'informations. | 
| **`mother.py` / `veronica.py`** | Supervision matérielle et protocoles de protection du système. | 
| **`david.py` / `sonny.py`** | Réflexion philosophique, dialogue contextuel et analyse comportementale. | 

## 5. Modules d'Analyse & Outillage

Outre les agents, JARVIS dispose de modules techniques autonomes situés dans `app/core/` :

* **`code_reader.py`** : Analyse le code source présent dans le projet ou soumis par l'utilisateur pour y repérer des erreurs de syntaxe ou des optimisations.

* **`log_analyzer.py`** : Inspecte les fichiers de journalisation (`.log`) pour diagnostiquer rapidement les pannes du système.

* **`system_stats.py`** : Récupère la charge CPU, la température, l'utilisation de la VRAM GPU et la mémoire disponible.

* **`email_manager.py`** : Permet la lecture et l'organisation des messages (protocoles IMAP/SMTP).

* **`actions.py`** : Déclenche des scripts PowerShell éphémères pour contrôler les applications Windows (VS Code, Chrome, Fusion 360, gestion du volume sonore, etc.).

## 6. Modes d'Interaction (Web & CLI)

### Interface Web HUD (`http://localhost:5000`)

* **Visualiseur 3D Three.js** : Représentation dynamique de la matrice neuronale.

* **Microphone / Vocal** : Écoute continue via `ears.py` (Whisper) et réponse parlée via `mouth.py` (`pyttsx3`).

* **WebSockets** : Échange bidirectionnel ultra-rapide sans rechargement de page.

### Terminal Dédié (`main_keyboard.py`)

Si l'interface graphique n'est pas nécessaire, exécutez le script CLI pour interagir directement en ligne de commande :

```
python3 main_keyboard.py

```

## 7. Résolution de Problèmes (Troubleshooting)

* **Erreur de connexion avec Ollama (`ConnectionRefusedError`)** :

  * Vérifiez l'adresse IP de la passerelle WSL avec `ip route show | grep default`.

  * Assurez-vous qu'Ollama accepte les connexions réseau externes sous Windows en définissant la variable d'environnement `OLLAMA_HOST=0.0.0.0` sur Windows.

* **Problème de Micro / PyAudio sous WSL** :

  * WSL2 ne redirige pas toujours les périphériques audio par défaut. Assurez-vous d'avoir configuré PulseAudio / WSLg ou utilisez le mode clavier via le HUD web ou `main_keyboard.py`.