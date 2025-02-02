class Subtopic:
    """
    Represents a subtopic within user insight.

    Attributes:
        subtopicID (str): Identifier for the subtopic.
        name (str): Name of the subtopic.
    """

    def __init__(self, subtopicID: str, name: str):
        self.subtopicID = subtopicID
        self.name = name

    def updateName(self, newName: str) -> None:
        """Update the name of the subtopic."""
        self.name = newName 