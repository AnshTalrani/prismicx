"""
Unit tests for auth.py
"""

import unittest
from src.auth import AuthService

class TestAuthService(unittest.TestCase):
    """
    Test suite for the AuthService class.
    """
    def setUp(self):
        """
        Initialize AuthService for tests.
        """
        self.auth_service = AuthService()
    
    def test_validate_token_valid(self):
        """
        Test that a valid token returns True.
        """
        self.assertTrue(self.auth_service.validate_token("dummy_valid_token"))
    
    def test_validate_token_invalid(self):
        """
        Test that an invalid token returns False.
        """
        self.assertFalse(self.auth_service.validate_token("invalid_token"))

if __name__ == '__main__':
    unittest.main() 