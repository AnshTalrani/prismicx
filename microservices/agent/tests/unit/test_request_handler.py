import unittest
from handlers.request_handler import RequestHandler
from services.requirement_analyzer import RequirementAnalyzer
from services.template_selector import TemplateSelector
from services.orchestrator import Orchestrator
from services.error_handler import ErrorHandler
from utils.logger import Logger
from models.request import Request
from communication.communication_base import CommunicationBase
from models.error_catalog import ErrorCatalog

class TestRequestHandler(unittest.TestCase):
    def setUp(self):
        logger = Logger()
        error_db = ErrorCatalog(...)
        communication_base = CommunicationBase(...)
        error_handler = ErrorHandler(logger, communication_base, error_db)
        analyzer = RequirementAnalyzer()
        selector = TemplateSelector(...)
        orchestrator = Orchestrator(..., error_handler, ...)  # Initialize ContextManager appropriately
        self.handler = RequestHandler(analyzer, selector, orchestrator, error_handler, logger)

    def test_receive_request_success(self):
        request = Request(user_id="123", purpose_id="etsy_listing")
        result = self.handler.handle_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')

    def test_receive_request_failure(self):
        # Simulate failure and verify error handling
        request = Request(user_id="123", purpose_id="invalid_purpose")
        with self.assertRaises(Exception):
            self.handler.handle_request(request)

if __name__ == '__main__':
    unittest.main()