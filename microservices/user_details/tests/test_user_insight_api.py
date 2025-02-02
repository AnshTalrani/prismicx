import unittest
from api.user_insight_api import app
import json

class TestUserInsightAPI(unittest.TestCase):
    """Unit tests for UserInsightAPI."""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_process_template_success(self):
        """Test processing template successfully."""
        payload = {
            "templateID": "template_123",
            "userID": "user_456"
        }
        response = self.app.post('/processTemplate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.get_data(as_text=True))

    def test_process_template_failure(self):
        """Test processing template with missing data."""
        payload = {
            "templateID": "template_123"
            # Missing userID
        }
        response = self.app.post('/processTemplate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main() 