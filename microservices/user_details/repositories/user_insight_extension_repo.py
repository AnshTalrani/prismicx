from models.user_insight_extension import UserInsightExtension
import pymongo
import os

class UserInsightExtensionRepo:
    """Repository for managing UserInsightExtension documents in MongoDB."""

    def __init__(self):
        """Initialize the repository with MongoDB connection."""
        self.client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['user_details_db']
        self.collection = self.db['user_insight_extensions']

    def save(self, extension: UserInsightExtension) -> None:
        """Save a UserInsightExtension document."""
        self.collection.insert_one(self._serialize(extension))

    def findByUserID(self, userID: str) -> list:
        """Find all UserInsightExtensions by userID."""
        return [self._deserialize(doc) for doc in self.collection.find({"userID": userID})]

    def _serialize(self, extension: UserInsightExtension) -> dict:
        """Serialize UserInsightExtension object to dictionary."""
        return {
            "userID": extension.userID,
            "templateID": extension.templateID,
            "metrics": extension.metrics,
            "batchID": extension.batchID,
            "timestamp": extension.timestamp
        }

    def _deserialize(self, data: dict) -> UserInsightExtension:
        """Deserialize dictionary to UserInsightExtension object."""
        return UserInsightExtension(
            userID=data['userID'],
            templateID=data['templateID'],
            metrics=data['metrics'],
            batchID=data['batchID']
        ) 