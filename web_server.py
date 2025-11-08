#!/usr/bin/env python3

"""
Servidor WebSocket para DexterMeetAgent
Proporciona interfaz web en tiempo real para transcripciones
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime
import logging

# Configurar logging mínimo
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dexter_meet_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebSocketServer:
    def __init__(self):
        self.clients_connected = 0
        self.recording_control_callback = None
        
    def set_recording_callback(self, callback):
        """Establece callback para controlar grabación en main.py"""
        self.recording_control_callback = callback
        
    def start_server(self):
        """Inicia el servidor WebSocket"""
        print("🌐 Servidor web iniciado en http://localhost:5001")
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True, use_reloader=False)
    
    def send_transcription(self, participant, message, timestamp=None):
        """Envía transcripción a todos los clientes conectados"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
        data = {
            'type': 'transcription',
            'participant': participant,
            'message': message,
            'timestamp': timestamp
        }
        socketio.emit('new_transcription', data)
        
    def send_response(self, message, timestamp=None):
        """Envía respuesta del asistente a todos los clientes conectados"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
        data = {
            'type': 'response',
            'message': message,
            'timestamp': timestamp
        }
        socketio.emit('new_response', data)
    
    def send_status(self, status, message):
        """Envía actualización de estado"""
        data = {
            'type': 'status',
            'status': status,
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        socketio.emit('status_update', data)

# Instancia global del servidor
web_server = WebSocketServer()

@app.route('/')
def index():
    """Página principal con la interfaz de transcripciones"""
    return render_template('index.html')

@app.route('/api/transcription', methods=['POST'])
def receive_transcription():
    """Recibe transcripción vía HTTP POST y la retransmite por WebSocket"""
    try:
        data = request.get_json()
        socketio.emit('new_transcription', data)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/response', methods=['POST'])
def receive_response():
    """Recibe respuesta vía HTTP POST y la retransmite por WebSocket"""
    try:
        data = request.get_json()
        socketio.emit('new_response', data)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/start_recording', methods=['POST'])
def start_recording():
    """Inicia grabación de audio controlada por el frontend"""
    try:
        print("🔴 API: Recibida solicitud de inicio de grabación")
        if web_server.recording_control_callback:
            result = web_server.recording_control_callback('start')
            print("✅ API: Grabación iniciada correctamente")
            return jsonify({'status': 'success', 'message': 'Grabación iniciada'}), 200
        else:
            print("❌ API: Callback no configurado")
            return jsonify({'status': 'error', 'message': 'Callback no configurado'}), 500
    except Exception as e:
        print(f"❌ API: Error iniciando grabación: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording():
    """Detiene grabación y procesa audio"""
    try:
        print("⏹️ API: Recibida solicitud de fin de grabación")
        if web_server.recording_control_callback:
            result = web_server.recording_control_callback('stop')
            print("✅ API: Grabación detenida, procesando...")
            return jsonify({'status': 'success', 'message': 'Grabación detenida, procesando...'}), 200
        else:
            print("❌ API: Callback no configurado")
            return jsonify({'status': 'error', 'message': 'Callback no configurado'}), 500
    except Exception as e:
        print(f"❌ API: Error deteniendo grabación: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    web_server.clients_connected += 1
    emit('connection_response', {
        'status': 'connected',
        'message': f'Conectado al servidor de transcripciones. Clientes activos: {web_server.clients_connected}'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    web_server.clients_connected = max(0, web_server.clients_connected - 1)

if __name__ == '__main__':
    web_server.start_server()