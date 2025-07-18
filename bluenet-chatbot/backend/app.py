from flask import Flask, request, jsonify
import sqlite3
import feedparser
from PIL import Image
import io
import polyline
from openai import OpenAI

app = Flask(__name__)

# --- Database Functions ---
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("knowledge_base.db")
    except sqlite3.error as e:
        print(e)
    return conn

# --- Bhashini API Placeholder ---
def translate_text(text, target_language):
    """
    This is a placeholder function for the Bhashini API.
    It currently does not perform any translation.
    """
    return text

# --- OpenRouter Integration ---
def get_openrouter_response(message):
    """
    This function sends a message to the OpenRouter API and returns the response.
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="YOUR_OPENROUTER_API_KEY", # Please replace with your API key
    )
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1",
            messages=[
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- Endpoints ---
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    translated_message = translate_text(user_message, "en")
    openrouter_response = get_openrouter_response(translated_message)

    if openrouter_response:
        response_text = openrouter_response
    else:
        response_text = "Sorry, I could not understand your message."

    return jsonify({"response": response_text})

@app.route('/kb', methods=['GET', 'POST'])
def kb():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
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
    # Placeholder for IMD RSS feed
    rss_url = "https://alerts.weather.gov/cap/us.php?x=1" # Using a sample RSS feed for now
    feed = feedparser.parse(rss_url)
    alerts = []
    for entry in feed.entries:
        alerts.append({
            "title": entry.title,
            "summary": entry.summary,
            "link": entry.link
        })
    return jsonify(alerts)

@app.route('/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if file:
        # Placeholder for fish identification
        # For now, we will just return a dummy prediction
        try:
            img = Image.open(io.BytesIO(file.read()))
            # In a real application, you would send the image to a fish identification API
            prediction = "This is a dummy prediction. The fish is a... Clownfish!"
            return jsonify({"prediction": prediction})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/navigate', methods=['POST'])
def navigate():
    # Placeholder for navigation
    # In a real application, you would use a mapping service to get the route
    # For now, we will just return a dummy route
    # The route is encoded using polyline encoding
    route = [
        (12.9716, 77.5946), # Bangalore
        (13.0827, 80.2707)  # Chennai
    ]
    encoded_route = polyline.encode(route)
    return jsonify({"route": encoded_route})

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

if __name__ == '__main__':
    # create a database connection
    conn = db_connection()
    # create table if it doesn't exist
    if conn is not None:
        sql_create_articles_table = """ CREATE TABLE IF NOT EXISTS articles (
                                        id integer PRIMARY KEY,
                                        title text NOT NULL,
                                        content text NOT NULL,
                                        language text NOT NULL
                                    ); """
        sql_create_users_table = """CREATE TABLE IF NOT EXISTS users (
            id integer PRIMARY KEY,
            fisher_id text UNIQUE,
            language text,
            location text
        );
        """
        try:
            c = conn.cursor()
            c.execute(sql_create_articles_table)
            c.execute(sql_create_users_table)
        except sqlite3.Error as e:
            print(e)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

    app.run(debug=True, port=5000)
