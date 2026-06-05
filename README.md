<p align="center"\>
<img src="https://github.com/Mathieu7483/JARVIS/blob/main/Gemini_Generated_Image_suuqetsuuqetsuuq.png"\>
</p>


# JARVIS — Assistant Personnel Domotique & IA Locale (v3.0)

JARVIS (Just Rather Very Intelligent System) est un assistant virtuel personnel conçu pour s'exécuter localement. Il intègre une interface web immersive en temps réel (**Flask & SocketIO**) couplée à un modèle de langage local (**Ollama / Llama 3.1:8b**), un système de mémoire persistante et des modules d'interaction vocale ou textuelle.

L'architecture est spécifiquement optimisée pour faire le pont entre un environnement de développement **WSL (Linux)** et un système hôte **Windows** (gestion réseau, exécution PowerShell et rendu graphique matériel).
Des évolutions auront lieues, ce projet est en cours de construction

---

## 🧠 Personnalité & Directives Système

Le comportement de JARVIS est régi par des directives strictes insufflées à son processeur central [cite: 2025-10-22] :

* **Ton et Posture** : Formel, calme, élégant et strictement professoral [cite: 2025-10-22]. Il s'adresse exclusivement à l'utilisateur en l'appelant **"Monsieur"**.
* **Honnêteté absolue** : Si une erreur de logique ou de programmation est détectée, JARVIS la signale directement et sans détour [cite: 2025-10-22].
* **Optimisation Vocale** : Les réponses excluent tout formatage Markdown (pas de listes à puces, pas de tirets, pas de symboles spéciaux) pour garantir une synthèse vocale fluide et naturelle.

---

## 🎨 Interface Utilisateur & Rendu Cybernétique (Front-End)

L'interface utilisateur (`index.html`) est conçue comme un affichage tête haute (HUD) futuriste, exploitant les technologies web les plus avancées :

### 1. Modélisation Neuronale en 3D (`Three.js`)

Le centre de l'écran est occupé par une représentation volumétrique tridimensionnelle du "cerveau" de JARVIS, chargée via une matrice de points géométriques complexes (`brain_points.json`).

* Le système génère dynamiquement des connexions synaptiques (lignes et impulsions lumineuses) en utilisant un algorithme d'évaluation de la distance euclidienne entre les nœuds.
* Les matériaux utilisent un mode de fusion additif (`THREE.AdditiveBlending`) pour accentuer l'effet de luminescence technologique.

### 2. Gestion Dynamique des États (WebSockets)

L'interface réagit en temps réel aux signaux émis par le serveur Flask grâce à `Socket.IO`. La coloration du système de particules et les animations s'adaptent instantanément à l'activité de JARVIS :

* 🔵 **Cyan (`idle`)** : Mode veille, rotation calme et pulsations régulières.
* 🟠 **Orange (`thinking`)** : Phase de réflexion du LLM. L'agitation synaptique s'accélère, la taille et l'opacité des particules s'intensifient.
* 🟢 **Vert (`speaking`)** : Phase de synthèse vocale ou de réponse. Le visualiseur audio CSS s'active.
* 🟣 **Violet (`keyboard`)** : Mode saisie manuelle.

### 3. Fonctionnalités de l'Interface

* **Double Mode d'Interaction** : Bascule instantanée via un commutateur dédié entre le mode **Vocal** (activation du microphone) et le mode **Clavier** (champ de saisie textuel asynchrone).
* **Affichage Typewriter** : Les réponses de JARVIS s'affichent lettre par lettre avec un curseur oscillant simulé, imitant un terminal en direct.
* **Historique de Session** : Un panneau latéral conserve un fil d'ariane visuel de l'ensemble des requêtes et réponses de la session en cours.

---

## 🛠️ Architecture Spécifique des Modules (Back-End)

### 1. Le Serveur Central (`app.py`)

Orchestre les communications bidirectionnelles. La boucle principale d'écoute/réflexion tourne dans un thread d'arrière-plan dédié, isolé du thread réseau de Flask pour éviter tout blocage de l'interface, sécurisé par un `Lock` mutuel. Le mode `debug=False` est impératif pour empêcher le rechargement double des modèles d'IA lourds.

### 2. Le Cerveau Connecté (`app/core/processor.py`)

Pilote le modèle `llama3.1:8b`. Il procède par classification d'intentions pour déterminer si la requête nécessite un outil externe (`WEATHER`, `SEARCH`, `MEMORIZE`, ou `NONE`), injecte le contexte temporel et historique, puis formule la réponse.

### 3. Mémoire Persistante (`app/core/memory.py`)

Gère la persistance sous forme de fichier JSON plat (`jarvis_memory.json`). Il contient le profil initial de l'utilisateur (Prénom, domaines d'étude) et se met à jour dynamiquement lorsque JARVIS isole un fait à mémoriser.

### 4. Exécuteur de Commandes Système (`app/actions.py`)

Permet à JARVIS de contrôler le système d'exploitation Windows hôte depuis l'environnement WSL en utilisant des scripts éphémères exécutés via **PowerShell** (`powershell.exe`).

* **Catalogue d'Applications** : Contrôle (lancement et arrêt forcé) d'outils de développement et de création (Google Chrome, VS Code, Discord, Windows Media Player, OpenOffice, Autodesk Fusion 360, Ultimaker Cura).
* **Contrôles Systèmes** : Gestion du volume (via l'envoi de touches virtuelles VBScript/PowerShell), captures d'écran automatiques et mise en veille matérielle de la machine.

---

## 📋 Prérequis & Configuration Matérielle

L'interface met fièrement en avant la configuration matérielle requise et ciblée pour une inférence locale fluide :

* **GPU cible** : NVIDIA GeForce RTX 3060 (12 GB VRAM requis pour charger confortablement le modèle quantifié 8B et les composants d'écoute).
* **STT Engine** : Whisper Medium.
* **LLM** : Llama 3.1 (8 milliards de paramètres) via Ollama.

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

### Configuration Réseau WSL ⇄ Windows

Ollama s'exécutant sur l'hôte Windows pour bénéficier de l'accélération GPU, l'adresse de liaison dans `config.py` pointe vers la passerelle réseau du sous-système Linux :

```python
OLLAMA_HOST = "http://172.21.176.1:11434"

```

---

## 🚀 Installation et Lancement

1. Assurez-vous qu'Ollama est actif sur Windows : `ollama run llama3.1:8b`.
2. Dans votre terminal WSL, installez les dépendances et lancez l'application :

```bash
cd ~/JARVIS
pip install -r requirements.txt
python3 app.py

```

3. Ouvrez votre navigateur sur **`http://localhost:5000`**.

---

## ✍️ Auteur

  * **Mathieu** - *Programming student, specialization Machine Learning* - [👤 My Github profile](https://github.com/Mathieu7483)
