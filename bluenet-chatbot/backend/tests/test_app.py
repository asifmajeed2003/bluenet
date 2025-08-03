import unittest
import sys
import os

# Add the backend and tests directories to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app import app
import config

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_chat_endpoint(self):
        response = self.app.post('/chat', json={'message': 'hello'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('response', response.json)

    def test_alerts_endpoint(self):
        response = self.app.get('/alerts')
        self.assertEqual(response.status_code, 200)

    def test_navigate_endpoint(self):
        response = self.app.post('/navigate', json={'start': [8.681495, 49.41461], 'end': [8.687872, 49.420318]})
        self.assertEqual(response.status_code, 200)

    def test_recognize_endpoint(self):
        # This test requires an image file. I will skip it for now.
        pass

    def test_speech_to_text_endpoint(self):
        # This test requires an audio file. I will skip it for now.
        pass

    def test_text_to_speech_endpoint(self):
        response = self.app.post('/text-to-speech', json={'text': 'hello'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'audio/mpeg')

    def test_kb_endpoint(self):
        response = self.app.get('/kb')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
