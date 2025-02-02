# Purpose: Tests the functionalities of the IdentifierService class.

import unittest
from services.identifier_service import IdentifierService
from models.request import Request
import uuid

class TestIdentifierService(unittest.TestCase):
    def setUp(self):
        self.identifier_service = IdentifierService()

    def test_generate_request_id(self):
        request_id = self.identifier_service.generate_request_id()
        self.assertIsNotNone(request_id)
        self.assertIsInstance(request_id, str)
        self.assertEqual(len(request_id), 32)  # Assuming hex UUID

    def test_assign_identifiers(self):
        request = Request(
            user_id="",
            purpose_id=""
        )
        analysis_result = self.identifier_service.assign_identifiers(request)
        self.assertIsNotNone(analysis_result.user_id)
        self.assertIsNotNone(analysis_result.purpose_id)
        self.assertIsNotNone(request.request_id)

if __name__ == '__main__':
    unittest.main() 