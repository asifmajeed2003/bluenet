from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import requests
import openrouteservice
from imageai.Detection import ObjectDetection
import os
from opencage.geocoder import OpenCageGeocode
import vosk
import wave
import json
from gtts import gTTS
import io
import sqlite3
import speech_recognition as sr
import translators as ts
from elevenlabs import Voice, VoiceSettings, generate, play, set_api_key

load_dotenv()

app = Flask(__name__)
CORS(app)

def translate(text, to_language, from_language='auto'):
    return ts.translate_text(text, to_language=to_language, from_language=from_language)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    language = request.json.get('language', 'en')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )

    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are Bluenet, a helpful assistant for Indian coastal fishing communities. You provide information on regulations, safety, and weather. You are friendly and speak in simple terms.",
                },
                {"role": "user", "content": user_message},
            ],
        )
        response_text = response.choices[0].message.content
        translated_response = translate(response_text, to_language=language)
        return jsonify({"response": translated_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/alerts', methods=['GET'])
def alerts():
    location = request.args.get('location', 'Chennai')  # Default location is Chennai
    api_key = os.environ.get("WEATHERSTACK_API_KEY")
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

@app.route('/navigate', methods=['POST'])
def navigate():
    start_coords = request.json.get('start')
    destination = request.json.get('destination')

    if not start_coords or not destination:
        return jsonify({"error": "Start coordinates and destination are required"}), 400

    geocoder = OpenCageGeocode(os.environ.get("OPENCAGE_API_KEY"))
    results = geocoder.geocode(destination)

    if not results or len(results) == 0:
        return jsonify({"error": "Could not find coordinates for the destination."}), 400

    end_coords = [results[0]['geometry']['lng'], results[0]['geometry']['lat']]

    client = openrouteservice.Client(key=os.environ.get("ORS_API_KEY"))

    try:
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='foot-walking',
            format='json'
        )
        return jsonify(routes)
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
        # Check if the file is an image
        if file.content_type.startswith('image/'):
            try:
                # Save the file to a temporary directory
                import tempfile
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, file.filename)
                file.save(file_path)

                return jsonify({"message": "Image uploaded successfully. Please send your query."})
            except Exception as e:
                return jsonify({"error": f"An error occurred during image upload: {e}"}), 500
        else:
            return jsonify({"error": "File is not an image"}), 400

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        try:
            if not os.environ.get("ELEVENLABS_API_KEY"):
                return jsonify({"error": "ElevenLabs API key not found."}), 500
            set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

            # Convert speech to text
            transcript = elevenlabs.speech_to_text(file)

            # Translate to English
            translated_transcript = translate(transcript, to_language='en')

            # Get response from chatbot
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ.get("OPENROUTER_API_KEY"),
            )
            response = client.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                messages=[
                    {
                        "role": "system",
                        "content": "You are Bluenet, a helpful assistant for Indian coastal fishing communities. You provide information on regulations, safety, and weather. You are friendly and speak in simple terms.",
                    },
                    {"role": "user", "content": translated_transcript},
                ],
            )
            response_text = response.choices[0].message.content

            # Translate response back to original language
            translated_response = translate(response_text, to_language=request.form.get('language', 'en'))

            return jsonify({"response": translated_response})
        except Exception as e:
            return jsonify({"error": f"An error occurred during speech-to-text: {e}"}), 500

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json.get('text')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        if not os.environ.get("ELEVENLABS_API_KEY"):
            return jsonify({"error": "ElevenLabs API key not found."}), 500
        set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

        audio = generate(
            text=text,
            voice=Voice(
                voice_id='21m00Tcm4TlvDq8ikWAM',
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            )
        )

        return audio, 200, {'Content-Type': 'audio/mpeg'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def init_db():
    conn = sqlite3.connect('bluenet.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route('/kb', methods=['GET', 'POST'])
def kb():
    init_db()
    conn = sqlite3.connect('bluenet.db')
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

@app.route('/image-chat', methods=['POST'])
def image_chat():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    message = request.form.get('message')
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if file:
        # Check if the file is an image
        if file.content_type.startswith('image/'):
            try:
                # Translate to English
                translated_message = translate(message, to_language='en')

                # Get response from chatbot
                client = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.environ.get("OPENROUTER_API_KEY"),
                )
                response = client.chat.completions.create(
                    model="meta-llama/llama-3.2-11b-vision-instruct:free",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are Bluenet, a helpful assistant for Indian coastal fishing communities. You provide information on regulations, safety, and weather. You are friendly and speak in simple terms.",
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": translated_message},
                                {"type": "image_url", "image_url": {"url": f"data:{file.content_type};base64,{file.read()}"}}
                            ]
                        },
                    ],
                )
                response_text = response.choices[0].message.content

                # Translate response back to original language
                translated_response = translate(response_text, to_language=request.form.get('language', 'en'))

                return jsonify({"response": translated_response})
            except Exception as e:
                return jsonify({"error": f"An error occurred during image processing: {e}"}), 500
        else:
            return jsonify({"error": "File is not an image"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
