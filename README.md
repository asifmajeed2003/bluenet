# Bluenet Chatbot

The Bluenet Chatbot is a light, multilingual voice-and-text assistant that provides important information to Indian coastal fishing communities. It is designed to work in areas with low literacy levels and patchy network connectivity.

## Features

*   **Multilingual Voice & Text Interface:** Supports regional languages and uses Google Cloud speech APIs and IndicTrans 2.0 for translation.
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
*   **NLP/AI:** OpenRouter (for chat), IndicTrans 2.0 (for translation)
*   **Voice Services:** Google Cloud Text-to-Speech & Speech-to-Text
*   **Weather Data:** WeatherAPI
*   **Fish Recognition:** Fishial API
*   **Navigation:** OpenRouteService API

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
    *   Populate the database with sample data:
        ```bash
        python populate_db.py
        ```
    *   **API Keys:** You will need to get API keys for the following services and add them to the `app.py` file:
        *   OpenRouter
        *   WeatherAPI
        *   Fishial API
        *   OpenRouteService
        *   Google Cloud Platform (for Speech-to-Text and Text-to-Speech)
    *   Run the Flask server:
        ```bash
        python app.py
        ```
3.  **Set up the frontend:**
    *   Open the `index.html` file in your browser.

## Usage

*   Open the chat interface in your browser.
*   Type a message in the input box and press Enter or click the send button.
*   Use the microphone button to speak to the chatbot.
*   Use the theme switcher to toggle between light and dark mode.
*   You can also use the following endpoints to interact with the backend:
    *   `/chat`: Send a chat message.
    *   `/translate`: Translate text.
    *   `/kb`: Manage the knowledge base.
    *   `/alerts`: Get the latest weather alerts.
    *   `/recognize`: Recognize a fish species from an image.
    *   `/navigate`: Get a safe route to the shore.
    *   `/users`: Manage user profiles.
    *   `/speech-to-text`: Convert speech to text.
    *   `/text-to-speech`: Convert text to speech.

## Creating a Presentation

Here are some key points to cover in a presentation about the Bluenet Chatbot:

*   **Introduction:**
    *   Problem: Lack of access to information for Indian coastal fishing communities.
    *   Solution: The Bluenet Chatbot, a multilingual voice-and-text assistant.
*   **Features:**
    *   Highlight the key features of the chatbot, such as regulatory guidance, safety protocols, environmental alerts, and media recognition.
    *   Showcase the multilingual and voice capabilities of the chatbot.
*   **Technology Stack:**
    *   Explain the technologies used to build the chatbot, including the frontend, backend, and various APIs.
    *   Discuss the benefits of using these technologies.
*   **System Architecture:**
    *   Provide an overview of the system architecture, including the user interface, application logic, and data integration layers.
    *   Explain how the different components of the system interact with each other.
*   **Demonstration:**
    *   Give a live demonstration of the chatbot, showcasing its key features.
    *   Show how the chatbot can be used to get information on regulations, safety, and weather.
*   **Impact:**
    *   Discuss the potential impact of the chatbot on the fishing communities, such as improved safety, compliance, and digital literacy.
*   **Future Work:**
    *   Talk about the future plans for the chatbot, such as adding more features and supporting more languages.
