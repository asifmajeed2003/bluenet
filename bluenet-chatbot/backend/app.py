from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import feedparser
from PIL import Image
import io
import polyline
from openai import OpenAI
import requests
import openrouteservice
from google.cloud import speech
from google.cloud import texttospeech
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

app = Flask(__name__)
CORS(app)

# --- IndicTrans 2.0 Setup ---
tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indictrans2-en-indic-1B", trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained("ai4bharat/indictrans2-en-indic-1B", trust_remote_code=True)

# --- Database Functions ---
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("bluenet.db")
    except sqlite3.error as e:
        print(e)
    return conn

# --- Language Detection Placeholder ---
def detect_language(text):
    """
    This is a placeholder function for language detection.
    It currently returns 'en' for all inputs.
    """
    # In a real application, you would use a language detection library or API
    return "en"

# --- IndicTrans 2.0 Translation ---
def translate_text(text, source_language, target_language):
    """
    This function translates text using the IndicTrans 2.0 model.
    """
    if source_language == target_language:
        return text

    # IndicTrans2 uses specific language codes
    lang_map = {
        "en": "eng_Latn",
        "hi": "hin_Deva",
        "ta": "tam_Taml",
        "te": "tel_Telu",
        "kn": "kan_Knda",
        "ml": "mal_Mlym",
    }

    src_lang_code = lang_map.get(source_language)
    tgt_lang_code = lang_map.get(target_language)

    if not src_lang_code or not tgt_lang_code:
        return text # Return original text if language is not supported

    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)

    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang_code],
            num_return_sequences=1,
            max_length=1024
        )

    decoded_tokens = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return decoded_tokens[0]

# --- OpenRouter Integration ---
def get_openrouter_response(message, history=[]):
    """
    This function sends a message to the OpenRouter API and returns the response.
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="YOUR_OPENROUTER_API_KEY",  # Please replace with your API key
    )
    try:
        messages = [
            {
                "role": "system",
                "content": "You are Bluenet, a helpful assistant for Indian coastal fishing communities. You provide information on regulations, safety, and weather. You are friendly and speak in simple terms.",
            }
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="deepseek/deepseek-r1",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- Endpoints ---
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    history = request.json.get('history', [])
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    source_language = detect_language(user_message)
    translated_message = translate_text(user_message, source_language, "en")

    openrouter_response = get_openrouter_response(translated_message, history)

    if openrouter_response:
        response_text = translate_text(openrouter_response, "en", source_language)
    else:
        response_text = "Sorry, I could not understand your message."

    return jsonify({"response": response_text})

@app.route('/translate', methods=['POST'])
def translate():
    text = request.json.get('text')
    source_language = request.json.get('source_language')
    target_language = request.json.get('target_language')

    if not text or not source_language or not target_language:
        return jsonify({"error": "Missing required parameters"}), 400

    translated_text = translate_text(text, source_language, target_language)
    return jsonify({"translated_text": translated_text})

@app.route('/kb', methods=['GET', 'POST'])
def kb():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        query = request.args.get('q')
        if query:
            cursor.execute("SELECT * FROM articles WHERE title LIKE ? OR content LIKE ?",
                           ('%' + query + '%', '%' + query + '%'))
        else:
            cursor.execute("SELECT * FROM articles")

        articles = [
            dict(id=row[0], title=row[1], content=row[2], language=row[3])
            for row in cursor.fetchall()
        ]
        if articles is not None:
            return jsonify(articles)

    if request.method == 'POST':
        new_title = request.form['title']
        new_content = request.form['content']
        new_language = request.form['language']
        sql = """INSERT INTO articles (title, content, language)
                 VALUES (?, ?, ?)"""
        cursor.execute(sql, (new_title, new_content, new_language))
        conn.commit()
        return f"Article with id: {cursor.lastrowid} created successfully", 201

@app.route('/alerts', methods=['GET'])
def alerts():
    location = request.args.get('location', 'Chennai')  # Default location is Chennai
    api_key = "YOUR_WEATHERAPI_KEY"  # Please replace with your API key
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=1&aqi=no&alerts=yes"

    try:
        response = requests.get(url)
        data = response.json()
        if "error" in data:
            return jsonify({"error": data["error"]["message"]}), 400

        alerts = data.get("alerts", {}).get("alert", [])
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        api_key = "YOUR_FISHIAL_API_KEY"  # Please replace with your API key
        url = "https://fishial.ai/api/v1/recognition"

        try:
            files = {'image': file.read()}
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.post(url, files=files, headers=headers)
            data = response.json()
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/navigate', methods=['POST'])
def navigate():
    api_key = "YOUR_ORS_API_KEY"  # Please replace with your API key
    client = openrouteservice.Client(key=api_key)

    start_coords = request.json.get('start')
    end_coords = request.json.get('end')

    if not start_coords or not end_coords:
        return jsonify({"error": "Start and end coordinates are required"}), 400

    try:
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='json'
        )
        return jsonify(routes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['GET', 'POST'])
def users():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM users")
        users = [
            dict(id=row[0], fisher_id=row[1], language=row[2], location=row[3])
            for row in cursor.fetchall()
        ]
        if users is not None:
            return jsonify(users)

    if request.method == 'POST':
        fisher_id = request.form['fisher_id']
        language = request.form['language']
        location = request.form['location']
        sql = """INSERT INTO users (fisher_id, language, location)
                 VALUES (?, ?, ?)"""
        cursor.execute(sql, (fisher_id, language, location))
        conn.commit()
        return f"User with id: {cursor.lastrowid} created successfully", 201

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=file.read())
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        try:
            response = client.recognize(config=config, audio=audio)
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            return jsonify({"transcript": transcript})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    try:
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content, 200, {'Content-Type': 'audio/mpeg'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
