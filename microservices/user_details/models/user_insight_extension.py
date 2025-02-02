from datetime import datetime
from typing import Any

class UserInsightExtension:
    """
    Represents an extension to a user's insight.

    Attributes:
        userID (str): Identifier for the user.
        templateID (str): Identifier for the template used.
        metrics (dict): JSON-formatted metrics data.
        batchID (str): Batch identifier.
        timestamp (datetime): Time of extension creation.
    """

    def __init__(self, userID: str, templateID: str, metrics: dict, batchID: str):
        self.userID = userID
        self.templateID = templateID
        self.metrics = metrics
        self.batchID = batchID
        self.timestamp = datetime.utcnow()

    def getMetrics(self) -> dict:
        """Retrieve the metrics."""
        return self.metrics

    def updateMetrics(self, newMetrics: dict) -> None:
        """Update the metrics."""
        self.metrics = newMetrics 