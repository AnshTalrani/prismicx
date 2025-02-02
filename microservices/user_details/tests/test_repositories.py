import unittest
from repositories.user_insight_repository import UserInsightRepository
from models.user_insight import UserInsight

class TestUserInsightRepository(unittest.TestCase):
    """Unit tests for UserInsightRepository."""

    def setUp(self):
        self.repo = UserInsightRepository()
        self.test_user_id = "test_user_1"
        self.insight = UserInsight(self.test_user_id)

    def test_create_and_find_insight(self):
        """Test creating and finding a UserInsight."""
        self.repo.create(self.test_user_id)
        found = self.repo.findById(self.test_user_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.userID, self.test_user_id)

    def test_delete_insight(self):
        """Test deleting a UserInsight."""
        self.repo.create(self.test_user_id)
        self.repo.delete(self.test_user_id)
        found = self.repo.findById(self.test_user_id)
        self.assertIsNone(found)

if __name__ == '__main__':
    unittest.main() 