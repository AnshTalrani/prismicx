from models.user_insight import UserInsight
import pymongo
import os

class UserInsightRepository:
    """Repository for managing UserInsight documents in MongoDB."""

    def __init__(self):
        """Initialize the repository with MongoDB connection."""
        self.client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['user_details_db']
        self.collection = self.db['user_insights']

    def findById(self, userID: str) -> UserInsight:
        """Find a UserInsight by userID."""
        data = self.collection.find_one({"userID": userID})
        if data:
            return self._deserialize(data)
        return None

    def save(self, insight: UserInsight) -> None:
        """Save a UserInsight document."""
        self.collection.update_one(
            {"userID": insight.userID},
            {"$set": self._serialize(insight)},
            upsert=True
        )

    def create(self, userID: str) -> UserInsight:
        """Create a new UserInsight."""
        insight = UserInsight(userID)
        self.save(insight)
        return insight
    
    def create_relavancy_points()

    def delete(self, userID: str) -> None:
        """Delete a UserInsight by userID."""
        self.collection.delete_one({"userID": userID})

    def _serialize(self, insight: UserInsight) -> dict:
        """Serialize UserInsight object to dictionary."""
        return {
            "userID": insight.userID,
            "topics": [topic.__dict__ for topic in insight.topics],
            "subtopics": [subtopic.__dict__ for subtopic in insight.subtopics],
            "practicalityID": insight.practicalityID,
            "batchIDs": insight.batchIDs
        }

    def _deserialize(self, data: dict) -> UserInsight:
        """Deserialize dictionary to UserInsight object."""
        insight = UserInsight(data['userID'])
        insight.topics = [Topic(**t) for t in data.get('topics', [])]
        insight.subtopics = [Subtopic(**s) for s in data.get('subtopics', [])]
        insight.practicalityID = data.get('practicalityID', '')
        insight.batchIDs = data.get('batchIDs', [])
        return insight 