"""
Unit tests for automation_engine.py
"""

import unittest
from src.automation_engine import AutomationEngine

class TestAutomationEngine(unittest.TestCase):
    """
    Test suite for the AutomationEngine.
    """
    def setUp(self):
        """
        Initialize AutomationEngine for tests.
        """
        self.user_id = "test_user"
        self.api_key = "dummy_api_key"
        self.engine = AutomationEngine(user_id=self.user_id, api_key=self.api_key)

    def test_process_template_no_conditions(self):
        """
        Test process_template when no conditions are met.
        """
        template = {}
        result = self.engine.process_template(template)
        self.assertEqual(result, "No conditions met for automation.")

    def test_process_template_with_condition(self):
        """
        Test process_template triggering condition.
        """
        template = {
            "conditions": {"balance_below": 1000}
        }
        result = self.engine.process_template(template)
        self.assertIn("Triggered notification and AI response", result)

    def test_send_notification(self):
        """
        Test send_notification by checking no exceptions are raised.
        """
        try:
            self.engine.send_notification("Test message", "test@example.com")
        except Exception as e:
            self.fail(f"send_notification raised an exception: {e}")

    def test_integrate_ai_assistant(self):
        """
        Test integrate_ai_assistant returns expected dummy response.
        """
        response = self.engine.integrate_ai_assistant("Test query")
        self.assertEqual(response, "AI suggestion: Consider optimizing finance workflows.")

if __name__ == "__main__":
    unittest.main() 