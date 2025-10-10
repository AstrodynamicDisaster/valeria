#!/usr/bin/env python3
"""
ValerIA Web Application
Flask-based web interface for the ValerIA agent
"""

import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from core.valeria_agent import ValeriaAgent

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='web', static_url_path='')
CORS(app)  # Enable CORS for development

# Configuration
UPLOAD_FOLDER = Path('./temp_uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Session storage (in-memory for prototype)
# In production, use Redis or database
sessions: Dict[str, Dict] = {}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_or_create_session(session_id: str) -> Dict:
    """Get existing session or create new one"""
    if session_id not in sessions:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        sessions[session_id] = {
            'agent': ValeriaAgent(api_key),
            'created_at': datetime.now().isoformat(),
            'history': []
        }

    return sessions[session_id]


@app.route('/')
def index():
    """Serve the main chat interface"""
    return send_from_directory('web', 'index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        if not session_id:
            session_id = str(uuid.uuid4())

        # Get or create session
        session = get_or_create_session(session_id)
        agent = session['agent']

        # Process message
        response = agent.run_conversation(message)

        # Store in history
        session['history'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        session['history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'response': response,
            'session_id': session_id
        })

    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        session_id = request.form.get('session_id')

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = UPLOAD_FOLDER / unique_filename

        file.save(str(file_path))

        # Get session
        session = get_or_create_session(session_id)

        # Store file info in history
        session['history'].append({
            'role': 'user',
            'content': f'[Uploaded file: {filename}]',
            'file_path': str(file_path),
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'message': f'File "{filename}" uploaded successfully',
            'file_path': str(file_path),
            'session_id': session_id
        })

    except Exception as e:
        app.logger.error(f"Error in upload endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history for a session"""
    try:
        session_id = request.args.get('session_id')

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        if session_id not in sessions:
            return jsonify({'history': []})

        session = sessions[session_id]
        return jsonify({'history': session['history']})

    except Exception as e:
        app.logger.error(f"Error in history endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """Clear a session"""
    try:
        data = request.json
        session_id = data.get('session_id')

        if session_id and session_id in sessions:
            del sessions[session_id]

        return jsonify({'message': 'Session cleared'})

    except Exception as e:
        app.logger.error(f"Error in clear endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get server statistics"""
    try:
        return jsonify({
            'active_sessions': len(sessions),
            'total_uploads': len(list(UPLOAD_FOLDER.glob('*'))),
        })

    except Exception as e:
        app.logger.error(f"Error in stats endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='ValerIA Web Interface')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print(f"🤖 ValerIA Web Interface starting...")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"📂 Upload folder: {UPLOAD_FOLDER.absolute()}")
    print(f"🔑 API Key: {'✓ Found' if os.getenv('OPENAI_API_KEY') else '✗ Missing'}")

    app.run(host=args.host, port=args.port, debug=args.debug)
