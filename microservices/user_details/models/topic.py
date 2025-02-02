class Topic:
    """
    Represents a topic within user insight.

    Attributes:
        topicID (str): Identifier for the topic.
        name (str): Name of the topic.
    """

    def __init__(self, topicID: str, name: str):
        self.topicID = topicID
        self.name = name

    def updateName(self, newName: str) -> None:
        """Update the name of the topic."""
        self.name = newName 