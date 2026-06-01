from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
import threading
import sys
import os
import time

# Ajoute le répertoire JARVIS au path
sys.path.insert(0, os.path.expanduser('~/JARVIS'))

from app.speech.ears import Ears
from app.speech.mouth import Mouth
from app.core.processor import Brain

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret'
# Utilisation de eventlet ou gevent est recommandée à terme, mais threading fonctionne pour le dev local
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialisation unique des composants lourds au démarrage du serveur
print("[JARVIS] Chargement des modules IA (Ears, Brain, Mouth)...")
ears = Ears()
brain = Brain()
mouth = Mouth()
print("[JARVIS] Modules chargés avec succès.")

jarvis_running = False
jarvis_thread = None
thread_lock = threading.Lock()  # Évite les conditions de concurrence sur la création du thread

def jarvis_loop():
    global jarvis_running
    print("[JARVIS] Boucle principale démarrée.")
    
    while jarvis_running:
        try:
            # 1. ÉCOUTE
            socketio.emit('status', {'state': 'listening'})
            texte = ears.ecouter()
            
            # Double vérification : si l'utilisateur a cliqué sur 'stop' pendant qu'on écoutait
            if not jarvis_running:
                break
                
            if not texte or len(texte.strip()) < 2:
                time.sleep(0.1)  # Léger répit pour le CPU
                continue
                
            socketio.emit('transcription', {'text': texte})
            
            # 2. RÉFLEXION
            socketio.emit('status', {'state': 'thinking'})
            reponse = brain.reflechir(texte)
            
            if not jarvis_running:
                break
                
            if not reponse:
                continue
                
            socketio.emit('response', {'text': reponse})
            
            # 3. PAROLE
            socketio.emit('status', {'state': 'speaking'})
            mouth.parler(reponse)
            
        except Exception as e:
            print(f"[JARVIS ERROR] Erreur dans la boucle : {e}", file=sys.stderr)
            socketio.emit('status', {'state': 'error', 'message': str(e)})
            time.sleep(1)  # Évite une boucle infinie ultra-rapide en cas de crash matériel continu

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
    texte = data.get('text', '').strip()
    if not texte:
        return
    socketio.emit('transcription', {'text': texte})
    socketio.emit('status', {'state': 'thinking'})
    reponse = brain.reflechir(texte)
    if reponse:
        socketio.emit('response', {'text': reponse})
        socketio.emit('status', {'state': 'speaking'})
        mouth.parler(reponse)
    socketio.emit('status', {'state': 'idle'})

    
if __name__ == '__main__':
    print("[JARVIS] Interface web disponible sur http://localhost:5000")
    # debug=False est impératif ici car le reloader de Flask instancierait tes modèles d'IA deux fois !
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)