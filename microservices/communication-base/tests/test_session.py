"""
Unit tests for session management.
"""

import unittest
import time
from src.session.session_manager import SessionManager

class TestSessionManager(unittest.TestCase):
    def test_session_creation_and_update(self):
        manager = SessionManager()
        session_id = "session1"
        manager.create_session(session_id, "initial")
        session = manager.get_session(session_id)
        self.assertEqual(session["state"], "initial")
        
        # Update session
        manager.update_session(session_id, "updated")
        session = manager.get_session(session_id)
        self.assertEqual(session["state"], "updated")
    
    def test_close_inactive_sessions(self):
        manager = SessionManager()
        session_id = "session2"
        manager.create_session(session_id, "data")
        # Simulate inactivity by artificially aging the session.
        time.sleep(1)
        manager.sessions[session_id]["last_active"] -= 3600  # Force it to be inactive.
        manager.close_inactive_sessions(timeout_seconds=300)
        self.assertIsNone(manager.get_session(session_id))

if __name__ == "__main__":
    unittest.main() 