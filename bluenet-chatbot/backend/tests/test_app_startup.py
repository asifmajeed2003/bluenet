import unittest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class TestAppStartup(unittest.TestCase):
    def test_app_import(self):
        self.assertIsNotNone(app)

if __name__ == '__main__':
    unittest.main()
