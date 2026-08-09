#!/usr/bin/env python3
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
import threading
import sys
import os
import time
import re

# Ajoute le répertoire JARVIS au path
sys.path.insert(0, os.path.expanduser('~/JARVIS'))

from app.speech.ears import Ears
from app.speech.mouth import Mouth
from app.core.processor import Brain
from app.core import system_stats

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret'
# Note: async_mode='gevent' ou 'eventlet' offre des performances accrues pour le streaming audio
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

print("[JARVIS] Chargement des modules IA (Ears, Brain, Mouth)...")
ears = Ears()
brain = Brain()
mouth = Mouth()
print("[JARVIS] Modules chargés avec succès.")

jarvis_running = False
jarvis_thread = None
telemetry_thread_started = False
thread_lock = threading.Lock()
audio_hardware_lock = threading.Lock()

def mother_telemetry_loop():
    """Tâche d'arrière-plan diffusant l'état CPU/RAM via WebSocket."""
    print("[MOTHER] Démarrage du flux de télémétrie...")
    while True:
        try:
            stats = system_stats.get_system_stats_dict()
            socketio.emit('mother_telemetry', {
                'cpu': stats.get('cpu', 0),
                'ram': stats.get('ram', 0)
            })
        except Exception as e:
            print(f"[MOTHER ERROR] Erreur télémétrie : {e}", file=sys.stderr)
        
        socketio.sleep(2)

@socketio.on('connect')
def handle_connect():
    global telemetry_thread_started
    with thread_lock:
        if not telemetry_thread_started:
            socketio.start_background_task(target=mother_telemetry_loop)
            telemetry_thread_started = True

def streamer_reponse_et_vocal(texte_input):
    """Génère la réponse d'Ollama token par token et émet le texte + audio fluide par morceau."""
    socketio.emit('status', {'state': 'speaking'})
    generateur_reponse = brain.reflechir(texte_input)
    
    phrase_buffer = ""
    texte_complet = []

    for token in generateur_reponse:
        if not jarvis_running and threading.current_thread() == jarvis_thread:
            break

        # 1. Emission temps réel du token texte au navigateur
        socketio.emit('response_chunk', {'text': token})
        phrase_buffer += token
        texte_complet.append(token)

        # 2. Découpage dynamique sur la ponctuation (., !, ?, ;) pour la vocalisation fluide
        if re.search(r'[.,?!;]\s*$', phrase_buffer):
            sub_phrase = phrase_buffer.strip()
            if len(sub_phrase) > 1:
                # Synthèse locale via Mouth (ou streaming audio)
                mouth.parler(sub_phrase)
            phrase_buffer = ""

    # Reliquat de fin de texte sans ponctuation
    if phrase_buffer.strip():
        sub_phrase = phrase_buffer.strip()
        mouth.parler(sub_phrase)
        
    texte_final = "".join(texte_complet).strip()
    socketio.emit('response_complete', {'text': texte_final})

def jarvis_loop():
    global jarvis_running
    print("[JARVIS] Boucle principale démarrée.")
    
    while jarvis_running:
        try:
            socketio.emit('status', {'state': 'listening'})
            
            with audio_hardware_lock:
                texte = ears.ecouter()
            
            if not jarvis_running:
                break
                
            if not texte or len(texte.strip()) < 2:
                time.sleep(0.1)
                continue
                
            socketio.emit('transcription', {'text': texte})
            socketio.emit('status', {'state': 'thinking'})
            socketio.emit('clear_response')
            
            if not jarvis_running:
                break

            with audio_hardware_lock:
                streamer_reponse_et_vocal(texte)
            
            time.sleep(0.2)
            
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

@socketio.on('stop')
def handle_stop():
    global jarvis_running
    with thread_lock:
        if jarvis_running:
            jarvis_running = False
            print("[JARVIS] Signal d'arrêt reçu.")

@socketio.on('text_input')
def handle_text_input(data):
    texte = data.get('text', '').strip()
    if not texte:
        return
        
    socketio.emit('transcription', {'text': texte})
    socketio.emit('status', {'state': 'thinking'})
    socketio.emit('clear_response')
    
    def run_async():
        with audio_hardware_lock:
            streamer_reponse_et_vocal(texte)
        socketio.emit('status', {'state': 'idle'})

    threading.Thread(target=run_async, daemon=True).start()

if __name__ == '__main__':
    print("[JARVIS] Interface web disponible sur http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)