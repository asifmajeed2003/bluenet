# Bluenet Chatbot

The Bluenet Chatbot is a light, multilingual voice-and-text assistant that provides important information to Indian coastal fishing communities. It is designed to work in areas with low literacy levels and patchy network connectivity.

## Features

*   **Multilingual Voice & Text Interface:** Supports regional languages and uses Google Cloud speech APIs.
*   **Regulatory Guidance Module:** Provides summaries of fishery regulations, conservation species, prohibited areas, and gear specifications.
*   **Safety Protocols Module:** Offers step-by-step life-jacket, distress, and first-aid procedures, as well as one-touch emergency workflows.
*   **Environmental Alerts Module:** Delivers live weather, tide, and cyclone warnings with push notifications.
*   **Operational Reminders Module:** Sends automatic license renewal and maintenance reminders through government portals.
*   **Offline Knowledge Base:** Caches FAQs, legal guidelines, and daily tips for low-connectivity regions.
*   **Media Recognition Module:** Identifies fish species from images to check for catch legality.
*   **Navigation & Route Guidance:** Provides voice-guided safe return routes without storm zones.
*   **User Profile & Personalization:** Stores language, location, and history.
*   **Daily Tips & Local News Feed:** Offers brief audio/text safety tips, local fisheries news, and a cultural fishing calendar.

## Technology Stack

*   **Frontend:** HTML5, CSS3, JavaScript
*   **Backend:** Python 3.x, Flask
*   **Database:** SQLite
*   **NLP/AI:** Rasa (intent classification), Bhashini API (translation)
*   **Voice Services:** Google Cloud Text-to-Speech & Speech-to-Text
*   **Data Sources:** IMD RSS feeds, government e-service APIs

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/bluenet-chatbot.git
    ```
2.  **Set up the backend:**
    *   Navigate to the `backend` directory:
        ```bash
        cd bluenet-chatbot/backend
        ```
    *   Install the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```
    *   Initialize the database:
        ```bash
        python database.py
        ```
    *   Run the Rasa server:
        ```bash
        rasa run -m models --enable-api --cors "*"
        ```
    *   Run the Flask server:
        ```bash
        python app.py
        ```
3.  **Set up the frontend:**
    *   Open the `index.html` file in your browser.

## Usage

*   Open the chat interface in your browser.
*   Type a message in the input box and press Enter or click the send button.
*   The chatbot will respond with the intent of your message.
*   You can also use the following endpoints to interact with the backend:
    *   `/chat`: Send a chat message.
    *   `/kb`: Manage the knowledge base.
    *   `/alerts`: Get the latest weather alerts.
    *   `/recognize`: Recognize a fish species from an image.
    *   `/navigate`: Get a safe route to the shore.
    *   `/users`: Manage user profiles.
