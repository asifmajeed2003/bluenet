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
from langdetect import detect
import speech_recognition as sr

load_dotenv()

app = Flask(__name__)
CORS(app)

def translate(text, target_language):
    try:
        tts = gTTS(text=text, lang=target_language)
        return tts.text
    except Exception as e:
        return text

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
            model="deepseek/deepseek-r1",
            messages=[
                {
                    "role": "system",
                    "content": "You are Bluenet, a helpful assistant for Indian coastal fishing communities. You provide information on regulations, safety, and weather. You are friendly and speak in simple terms.",
                },
                {"role": "user", "content": user_message},
            ],
        )
        response_text = response.choices[0].message.content
        translated_response = translate(response_text, language)
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
        try:
            # Save the file to a temporary directory
            import tempfile
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)

            detector = ObjectDetection()
            detector.setModelTypeAsYOLOv3()
            detector.setModelPath(os.path.join(temp_dir , "yolov3.pt"))
            detector.loadModel()
            detections = detector.detectObjectsFromImage(input_image=file_path, output_image_path=os.path.join(temp_dir , "imagenew.jpg"), minimum_percentage_probability=30)

            predictions = []
            for eachObject in detections:
                predictions.append({
                    "box": eachObject["box_points"],
                    "score": eachObject["percentage_probability"],
                    "label": eachObject["name"]
                })

            return jsonify({"predictions": predictions})
        except Exception as e:
            return jsonify({"error": f"An error occurred during speech recognition: {e}"}), 500

def detect_audio_language(audio_file):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        # Recognize speech using Google Speech Recognition
        text = r.recognize_google(audio)
        # Detect language from the recognized text
        lang = detect(text)
        return lang, text
    except sr.UnknownValueError:
        return None, None
    except sr.RequestError:
        return None, None

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        try:
            # Detect the language of the audio
            lang, text = detect_audio_language(file)
            if not lang:
                return jsonify({"error": "Could not detect language from audio"}), 500

            # Load the model
            model_path = f"vosk-model-small-{lang}-0.15"
            if not os.path.exists(model_path):
                return jsonify({"error": f"Vosk model for language '{lang}' not found."}), 500

            model = vosk.Model(model_path)

            # Process the audio file
            wf = wave.open(file, "rb")
            rec = vosk.KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    pass

            # Get the transcript
            result = json.loads(rec.FinalResult())
            transcript = result['text']

            return jsonify({"transcript": transcript, "language": lang})
        except Exception as e:
            return jsonify({"error": f"An error occurred during speech-to-text: {e}"}), 500

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
