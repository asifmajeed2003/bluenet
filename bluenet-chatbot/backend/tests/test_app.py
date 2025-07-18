import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bluenet_chatbot.backend.app import app

class TestChatbot(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('bluenet_chatbot.backend.app.OpenAI')
    def test_chat_endpoint(self, mock_openai):
        # Mock the OpenAI client and its response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, this is a test response."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Send a POST request to the /chat endpoint
        response = self.app.post('/chat',
                                 data=json.dumps({'message': 'Hello'}),
                                 content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['response'], "Hello, this is a test response.")

if __name__ == '__main__':
    unittest.main()
