import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import config
import requests
import openrouteservice
from ultralytics import YOLO
from PIL import Image
import io
import speech_recognition as sr
from gtts import gTTS
import sqlite3
import httpx

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.OPENROUTER_API_KEY,
        http_client=httpx.Client(proxies={}),
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
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        print(f"An error occurred in the chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

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
        print(f"An error occurred in the alerts endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/navigate', methods=['POST'])
def navigate():
    start_coords = request.json.get('start')
    end_coords = request.json.get('end')

    if not start_coords or not end_coords:
        return jsonify({"error": "Start and end coordinates are required"}), 400

    client = openrouteservice.Client(key=config.ORS_API_KEY)

    try:
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='json'
        )
        return jsonify(routes)
    except Exception as e:
        print(f"An error occurred in the navigate endpoint: {e}")
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
            # Load the model
            model = YOLO('yolov8n.pt')

            # Preprocess the image
            image = Image.open(file).convert('RGB')

            # Run inference
            results = model(image)

            # Postprocess the output
            predictions = []
            for result in results:
                for box in result.boxes:
                    predictions.append({
                        "box": box.xyxy[0].tolist(),
                        "score": box.conf[0].item(),
                        "label": model.names[int(box.cls[0].item())]
                    })

            return jsonify({"predictions": predictions})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        r = sr.Recognizer()
        with sr.AudioFile(file) as source:
            audio = r.record(source)
        try:
            transcript = r.recognize_google(audio)
            return jsonify({"transcript": transcript})
        except sr.UnknownValueError:
            return jsonify({"error": "Google Speech Recognition could not understand audio"}), 500
        except sr.RequestError as e:
            return jsonify({"error": f"Could not request results from Google Speech Recognition service; {e}"}), 500
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
