"""
Unit tests for notifications.py
"""

import unittest
from src.notifications import NotificationService

class TestNotificationService(unittest.TestCase):
    """
    Test suite for the NotificationService class.
    """
    def setUp(self):
        """
        Initialize NotificationService for tests.
        """
        self.notification_service = NotificationService()
    
    def test_send_email_success(self):
        """
        Test that sending an email returns True.
        """
        result = self.notification_service.send_email("Test Subject", "Test Message", "test@example.com")
        self.assertTrue(result)
    
    def test_send_sms_success(self):
        """
        Test that sending an SMS returns True.
        """
        result = self.notification_service.send_sms("Test SMS", "+123456789")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main() 