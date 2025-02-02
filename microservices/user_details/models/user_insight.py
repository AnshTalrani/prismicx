from typing import List
from .topic import Topic
from .subtopic import Subtopic
from .practicality import Practicality

class UserInsight:
    """
    Represents a user's insight data.

    Attributes:
        userID (str): Primary key identifier for the user.
        topics (List[Topic]): List of topics associated with the insight.
        subtopics (List[Subtopic]): List of subtopics.
        practicalityID (str): Foreign key linking to Practicality.
        batchIDs (List[str]): List of batch identifiers.
    """

    def __init__(self, userID: str):
        self.userID = userID
        self.topics: List[Topic] = []
        self.subtopics: List[Subtopic] = []
        self.practicalityID = ""
        self.batchIDs: List[str] = []

    def getTopics(self) -> List[Topic]:
        """Retrieve the list of topics."""
        return self.topics

    def addSubtopic(self, subtopic: Subtopic) -> None:
        """Add a subtopic to the user insight."""
        self.subtopics.append(subtopic)

    def removeSubtopic(self, subtopicID: str) -> None:
        """Remove a subtopic by its ID."""
        self.subtopics = [s for s in self.subtopics if s.subtopicID != subtopicID]

    def updateTopics(self, newTopics: List[Topic]) -> None:
        """Update the topics list."""
        self.topics = newTopics 