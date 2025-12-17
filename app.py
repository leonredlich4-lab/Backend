from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

DEEPSEEK_API_KEY = "sk-780fcc3b9b7f4c0ebc76cba4032b0502"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

conversations = {}

@app.route('/')
def home():
    return jsonify({"status": "Backend läuft", "service": "Pluro AI Chat API"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        user_id = request.remote_addr
        
        if not user_message:
            return jsonify({'error': 'Keine Nachricht'}), 400
        
        # Konversation für diesen User starten/fortsetzen
        if user_id not in conversations:
            conversations[user_id] = []
        
        conversations[user_id].append({"role": "user", "content": user_message})
        
        # Nachrichten für API vorbereiten
        messages = [
            {
                "role": "system",
                "content": "Du bist Pluro, ein hilfreicher KI-Assistent. Antworte natürlich und menschlich auf Deutsch."
            }
        ]
        
        # Nur die letzten 4 Nachrichten senden (für Kontext)
        history = conversations[user_id][-4:] if len(conversations[user_id]) > 4 else conversations[user_id]
        for msg in history:
            messages.append(msg)
        
        # DeepSeek API Aufruf
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': messages,
            'stream': False,
            'max_tokens': 1000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            
            # KI-Antwort zur Historie hinzufügen
            conversations[user_id].append({"role": "assistant", "content": ai_response})
            
            # Historie auf 10 Nachrichten begrenzen
            if len(conversations[user_id]) > 10:
                conversations[user_id] = conversations[user_id][-10:]
            
            return jsonify({
                'response': ai_response,
                'sender': 'Pluro'
            })
        else:
            return jsonify({
                'error': f'API Error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
