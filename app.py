from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import sys
import os

# Ajoute le répertoire JARVIS au path
sys.path.insert(0, os.path.expanduser('~/JARVIS'))

from ears import Ears
from app.core.processor import Brain
from mouth import Mouth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

ears = Ears()
brain = Brain()
mouth = Mouth()

jarvis_running = False

def jarvis_loop():
    global jarvis_running
    jarvis_running = True
    while jarvis_running:
        socketio.emit('status', {'state': 'listening'})
        texte = ears.ecouter()
        if not texte or len(texte.strip()) < 2:
            continue
        socketio.emit('transcription', {'text': texte})
        socketio.emit('status', {'state': 'thinking'})
        reponse = brain.reflechir(texte)
        if not reponse:
            continue
        socketio.emit('response', {'text': reponse})
        socketio.emit('status', {'state': 'speaking'})
        mouth.parler(reponse)
        socketio.emit('status', {'state': 'listening'})

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/static/models/<path:filename>')
def serve_model(filename):
    return send_from_directory('static/models', filename)

@socketio.on('start')
def handle_start():
    t = threading.Thread(target=jarvis_loop, daemon=True)
    t.start()

@socketio.on('stop')
def handle_stop():
    global jarvis_running
    jarvis_running = False

if __name__ == '__main__':
    print("[JARVIS] Interface web disponible sur http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)