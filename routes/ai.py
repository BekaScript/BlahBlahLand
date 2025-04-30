from flask import Blueprint, request, jsonify, session, current_app
from groq import Groq
import json
from models import db, Setting

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
        # Initialize Groq client
        client = Groq(
            api_key=current_app.config['GROQ_API_KEY'],
        )

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly assistant focused on generating short and clear messages. Speak in russian if user writes you in russian; otherwise, speak in english only. Make sure your answers do not exceed 30 words if not necessary. Your goal is to generate responses that users can easily copy and paste without needing to alter the text. You will not suggest multiple options. Always provide a direct, yet a creative response to the user's request."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            model="llama3-8b-8192",  # Using a default Groq model
        )

        # Extract the AI's response
        ai_message = chat_completion.choices[0].message.content

        return jsonify({
            "success": True,
            "ai_response": ai_message
        })

    except Exception as e:
        error_message = str(e)
        return jsonify({
            "success": False,
            "message": f"Error connecting to AI service: {error_message}"
        }), 500

@ai.route('/api/translate', methods=['POST'])
def translate_message():
    """
    Translate a message between English and Russian
    """
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    message_text = data.get('message')

    if not message_text:
        return jsonify({"success": False, "message": "Message text is required"}), 400

    try:
        # Initialize Groq client
        client = Groq(
            api_key=current_app.config['GROQ_API_KEY'],
        )

        # Determine the language and create the appropriate system prompt
        # Simple detection of Russian text (contains Cyrillic characters)
        has_cyrillic = any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in message_text)
        
        if has_cyrillic:
            target_language = "English"
            source_language = "Russian"
        else:
            target_language = "Russian"
            source_language = "English"

        # Create system prompt for translation
        system_prompt = f"""
You are a precise and professional translator that accurately translates text from {source_language} to {target_language}.
Follow these strict guidelines:
1. Provide ONLY the translated text with no additional commentary, explanations, or formatting.
2. Preserve the original tone, intent, and style of the message as closely as possible.
3. If the input is gibberish, nonsensical text, or in a language that is neither {source_language} nor {target_language}, DO NOT attempt to make jokes, create creative interpretations, or translate to anything except the literal text.
4. For nonsensical input like random characters (e.g., "asdfghjkl" or "jldskfj"), simply echo the exact same text back without translation.
5. Never generate text in languages other than {target_language}, even if the input seems like gibberish.
6. Do not add emojis, hashtags, or any content not present in the original message.
7. IMPORTANT: For acronyms and abbreviations like "jpa", "pdf", "html", etc.:
   - DO NOT expand them into their full meaning (e.g., do not translate "jpa" as "Java Persistence API")
   - If translating to Russian, transliterate Latin acronyms into Cyrillic (e.g., "jpa" → "джпа")
   - If translating to English, transliterate Cyrillic acronyms into Latin characters
   - Only translate acronyms if they have widely-used equivalent abbreviations in the target language

Remember: You are a strict, professional translator tool - not a creative AI or a technical dictionary.
"""

        # Call Groq API for translation
        translation = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message_text
                }
            ],
            model="llama3-8b-8192",  # Using a default Groq model
        )

        # Extract the translation
        translated_text = translation.choices[0].message.content

        return jsonify({
            "success": True,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language
        })

    except Exception as e:
        error_message = str(e)
        return jsonify({
            "success": False,
            "message": f"Error translating message: {error_message}"
        }), 500

def check_message_moderation(message_text, blocked_hashtags=None):
    """
    Use AI to check if a message contains inappropriate content based on blocked hashtags
    Returns a tuple (is_appropriate, reason)
    """
    try:
        # Get blocked hashtags if not provided
        if blocked_hashtags is None:
            setting = Setting.query.filter_by(key='blocked_hashtags').first()
            if setting and setting.value:
                blocked_hashtags = json.loads(setting.value)
            else:
                blocked_hashtags = []
        
        # Create the system prompt that includes the blocked hashtags
        system_prompt = f"""
You are a content moderation assistant. Your task is to evaluate if a message contains inappropriate content.

Specifically, check if the message contains:
1. Any of these blocked words or terms (in any case, partial match is allowed): {', '.join(blocked_hashtags)}
2. Any content that appears to have similar meaning or intent as the blocked terms
3. Any other generally offensive, harmful, or inappropriate content

If the message is inappropriate, return "INAPPROPRIATE:[reason]".
If the message is appropriate, return "APPROPRIATE".

Be strict and make sure to catch inappropriate content even when it uses euphemisms, indirect language, or is disguised in some way.
"""

        # Initialize Groq client
        client = Groq(
            api_key=current_app.config['GROQ_API_KEY'],
        )

        # Call Groq API for moderation check
        moderation_check = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message_text
                }
            ],
            model="llama3-8b-8192",  # Using a default Groq model
        )

        # Extract the AI's moderation decision
        response = moderation_check.choices[0].message.content.strip()
        
        if response.startswith("INAPPROPRIATE:"):
            reason = response[14:].strip()
            return (False, reason)
        else:
            return (True, "")

    except Exception as e:
        print(f"Error in AI moderation: {str(e)}")
        # If there's an error, allow the message through
        return (True, "")

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