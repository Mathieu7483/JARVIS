#!/usr/bin/env python3
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
import threading
import asyncio
import sys
import os
import time

# Ajoute le répertoire JARVIS au path pour l'importation de tes modules
sys.path.insert(0, os.path.expanduser('~/JARVIS'))

from app.speech.ears import Ears
from app.speech.mouth import Mouth
from app.core.processor import Brain

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret'
# Utilisation du mode threading pour le développement local
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialisation unique des composants lourds au démarrage du serveur
print("[JARVIS] Chargement des modules IA (Ears, Brain, Mouth)...")
ears = Ears()
brain = Brain()
mouth = Mouth()
print("[JARVIS] Modules chargés avec succès.")

jarvis_running = False
jarvis_thread = None
thread_lock = threading.Lock()         # Gestion de la concurrence sur le cycle du thread global
audio_hardware_lock = threading.Lock() # Protection stricte de la carte son (Écoute VS Parole)

def jarvis_loop():
    global jarvis_running
    print("[JARVIS] Boucle principale démarrée.")
    
    while jarvis_running:
        try:
            # 1. ÉCOUTE MATÉRIELLE SÉCURISÉE
            socketio.emit('status', {'state': 'listening'})
            
            with audio_hardware_lock:
                texte = ears.ecouter()
            
            if not jarvis_running:
                break
                
            if not texte or len(texte.strip()) < 2:
                time.sleep(0.2)  # Pause pour soulager le CPU
                continue
                
            socketio.emit('transcription', {'text': texte})
            
            # 2 & 3. RÉFLEXION ET PAROLE EN STREAMING ASYNCHRONE
            socketio.emit('status', {'state': 'thinking'})
            socketio.emit('clear_response') # Demande à l'interface de vider la boîte de dialogue précédente
            
            if not jarvis_running:
                break

            # Fonction locale asynchrone pour intercepter et diffuser le flux de jetons
            async def executer_flux_vocal():
                generateur_reponse = brain.reflechir(texte)
                socketio.emit('status', {'state': 'speaking'})
                
                # Liste pour reconstruire la phrase complète
                phrase_complete = []

                async def extraire_et_emettre(gen):
                    async for token in gen:
                        socketio.emit('response_chunk', {'text': token})
                        phrase_complete.append(token) # On stocke le token
                        yield token

                await mouth.consommer_et_parler(extraire_et_emettre(generateur_reponse))
                
                # Le flux est fini, on envoie la phrase complète à l'historique
                texte_final = "".join(phrase_complete).strip()
                socketio.emit('response_complete', {'text': texte_final})

            # Verrouillage de l'accès matériel pour la phase de génération et de diction
            with audio_hardware_lock:
                asyncio.run(executer_flux_vocal())
            
            # Légère temporisation pour permettre aux pilotes de l'OS de respirer
            time.sleep(0.3)
            
        except Exception as e:
            print(f"[JARVIS ERROR] Erreur dans la boucle principale : {e}", file=sys.stderr)
            socketio.emit('status', {'state': 'error', 'message': str(e)})
            time.sleep(1)

    print("[JARVIS] Boucle principale arrêtée proprement.")
    socketio.emit('status', {'state': 'idle'})

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/static/models/<path:filename>')
def serve_model(filename):
    return send_from_directory('static/models', filename)

@socketio.on('start')
def handle_start():
    global jarvis_running, jarvis_thread
    with thread_lock:
        if not jarvis_running:
            jarvis_running = True
            jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
            jarvis_thread.start()
            print("[JARVIS] Signal de démarrage reçu.")
        else:
            print("[JARVIS] Demande de démarrage ignorée : déjà en cours d'exécution.")

@socketio.on('stop')
def handle_stop():
    global jarvis_running
    with thread_lock:
        if jarvis_running:
            jarvis_running = False
            print("[JARVIS] Signal d'arrêt reçu. Arrêt au prochain cycle disponible...")

@socketio.on('text_input')
def handle_text_input(data):
    """Gestion des entrées manuelles textuelles depuis l'interface graphique."""
    texte = data.get('text', '').strip()
    if not texte:
        return
        
    socketio.emit('transcription', {'text': texte})
    socketio.emit('status', {'state': 'thinking'})
    socketio.emit('clear_response')
    
    async def executer_flux_clavier():
        generateur_reponse = brain.reflechir(texte)
        socketio.emit('status', {'state': 'speaking'})
        
        phrase_complete = []

        async def extraire_et_emettre(gen):
            async for token in gen:
                socketio.emit('response_chunk', {'text': token})
                phrase_complete.append(token)
                yield token

        await mouth.consommer_et_parler(extraire_et_emettre(generateur_reponse))
        
        texte_final = "".join(phrase_complete).strip()
        socketio.emit('response_complete', {'text': texte_final})

    # Sécurisation matérielle pour éviter toute interférence avec une écoute micro en cours
    with audio_hardware_lock:
        asyncio.run(executer_flux_clavier())
        
    socketio.emit('status', {'state': 'idle'})

if __name__ == '__main__':
    print("[JARVIS] Interface web disponible sur http://localhost:5000")
    # debug=False est impératif pour empêcher la double instanciation des modèles d'IA par le reloader Flask
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)