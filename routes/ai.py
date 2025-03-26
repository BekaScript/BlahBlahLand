from flask import Blueprint, request, jsonify, session, current_app
import requests
import json
from models import db

ai = Blueprint('ai', __name__)

@ai.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({"success": False, "message": "Message is required"}), 400

    try:
        # Call OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {current_app.config['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
                # "HTTP-Referer": "https://blahblahland.com", # You can update this
                "X-Title": "BlahBlahLand", # You can update this
            },
            json={
                "model": "google/gemma-3-27b-it:free",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a friendly assistant focused on generating short and clear messages. Speak in russian if user writes you in russian; otherwise, speak in english only. Make sure your answers do not exceed 30 words if not necessary. Your goal is to generate responses that users can easily copy and paste without needing to alter the text. You will not suggest multiple options. Always provide a direct, yet a creative response to the user's request."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            },
            timeout=10  # Add timeout to prevent hanging
        )

        # Check if the request was successful
        response.raise_for_status()

        # Extract the AI's response
        ai_response = response.json()
        ai_message = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')

        return jsonify({
            "success": True,
            "ai_response": ai_message
        })

    except requests.exceptions.RequestException as e:
        error_message = str(e)
        return jsonify({
            "success": False,
            "message": f"Error connecting to AI service: {error_message}"
        }), 500

@ai.route('/api/ai-chat/history', methods=['GET'])
def get_ai_chat_history():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    # In a real app, you might store AI chat history in the database
    # For this simple project, we'll just return a placeholder
    
    return jsonify({
        "success": True,
        "history": [
            # This would be populated from a database in a real app
        ]
    }) 