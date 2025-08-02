import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class TestChatbot(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.get_openrouter_response')
    def test_chat_endpoint(self, mock_get_openrouter_response):
        mock_get_openrouter_response.return_value = "Hello, this is a test response."
        response = self.app.post('/chat',
                                 data=json.dumps({'message': 'Hello'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("Translated from en to en: Hello, this is a test response.", data['response'])

    def test_translate_endpoint(self):
        response = self.app.post('/translate',
                                 data=json.dumps({'text': 'Hello', 'source_language': 'en', 'target_language': 'fr'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['translated_text'], "Translated from en to fr: Hello")

    @patch('app.db_connection')
    def test_kb_endpoint(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'Test Title', 'Test Content', 'en')
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_db_connection.return_value = mock_conn

        response = self.app.get('/kb')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Title')

    @patch('app.requests.get')
    def test_alerts_endpoint(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"alerts": {"alert": [{"title": "Test Alert"}]}}
        mock_get.return_value = mock_response

        response = self.app.get('/alerts')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Alert')

    @patch('app.requests.post')
    def test_recognize_endpoint(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"prediction": "Test Fish"}
        mock_post.return_value = mock_response

        with open('test.jpg', 'wb') as f:
            f.write(b"test")

        with open('test.jpg', 'rb') as f:
            response = self.app.post('/recognize',
                                     data={'file': (f, 'test.jpg')},
                                     content_type='multipart/form-data')

        os.remove('test.jpg')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['prediction'], 'Test Fish')

    @patch('app.openrouteservice.Client')
    def test_navigate_endpoint(self, mock_ors_client):
        mock_client = MagicMock()
        mock_client.directions.return_value = {"routes": "Test Route"}
        mock_ors_client.return_value = mock_client

        response = self.app.post('/navigate',
                                 data=json.dumps({'start': [8.48, 76.94], 'end': [8.52, 76.93]}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['routes'], 'Test Route')

    @patch('app.speech.SpeechClient')
    def test_speech_to_text_endpoint(self, mock_speech_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_response.results[0].alternatives = [MagicMock()]
        mock_response.results[0].alternatives[0].transcript = "Hello"
        mock_client.recognize.return_value = mock_response
        mock_speech_client.return_value = mock_client

        with open('test.wav', 'wb') as f:
            f.write(b"test")

        with open('test.wav', 'rb') as f:
            response = self.app.post('/speech-to-text',
                                     data={'file': (f, 'test.wav')},
                                     content_type='multipart/form-data')

        os.remove('test.wav')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['transcript'], 'Hello')

    @patch('app.texttospeech.TextToSpeechClient')
    def test_text_to_speech_endpoint(self, mock_tts_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"test"
        mock_client.synthesize_speech.return_value = mock_response
        mock_tts_client.return_value = mock_client

        response = self.app.post('/text-to-speech',
                                 data=json.dumps({'text': 'Hello'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"test")

if __name__ == '__main__':
    unittest.main()
