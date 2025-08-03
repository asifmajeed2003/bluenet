from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import feedparser
from PIL import Image
import io
import polyline
from openai import OpenAI
import requests
import speech_recognition as sr
from gtts import gTTS
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import config
import io

app = Flask(__name__)
CORS(app)

# --- IndicTrans 2.0 Setup ---
# The IndicTrans 2.0 model is very large and causes the application to time out on startup.
# I am replacing the translation functionality with a placeholder.

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
    This is a placeholder function for translation.
    It currently returns the original text.
    """
    return text

# --- OpenRouter Integration ---
import httpx

def get_openrouter_response(message, history=[]):
    """
    This function sends a message to the OpenRouter API and returns the response.
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_API_KEY,
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
    api_key = config.WEATHERSTACK_API_KEY
    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={location}"

    try:
        response = requests.get(url)
        data = response.json()
        if "error" in data:
            return jsonify({"error": data["error"]["info"]}), 400

        # Weatherstack API has a different response structure for alerts
        # This is a placeholder, as the free plan does not include alerts.
        # In a real application, you would parse the response to extract the relevant weather information.
        return jsonify(data)
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
        api_key = config.FISHIAL_API_KEY
        url = "https://fishial.ai/api/v1/recognition"

        try:
            files = {'image': file.read()}
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.post(url, files=files, headers=headers)
            data = response.json()
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

import openrouteservice

@app.route('/navigate', methods=['POST'])
def navigate():
    api_key = config.ORS_API_KEY
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
        # The audio file should be in WAV format for CMU Sphinx.
        # The frontend should handle the conversion before sending the file.
        r = sr.Recognizer()
        with sr.AudioFile(file) as source:
            audio = r.record(source)
        try:
            transcript = r.recognize_sphinx(audio)
            return jsonify({"transcript": transcript})
        except sr.UnknownValueError:
            return jsonify({"error": "Sphinx could not understand audio"}), 500
        except sr.RequestError as e:
            return jsonify({"error": f"Sphinx error; {e}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read(), 200, {'Content-Type': 'audio/mpeg'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"An error occurred: {e}")
