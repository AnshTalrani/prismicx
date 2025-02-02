class Factor:
    """
    Represents a factor influencing user insight.

    Attributes:
        factorID (str): Identifier for the factor.
        name (str): Name of the factor.
        description (str): Description of the factor.
    """

    def __init__(self, factorID: str, name: str, description: str):
        self.factorID = factorID
        self.name = name
        self.description = description

    def updateName(self, newName: str) -> None:
        """Update the name of the factor."""
        self.name = newName

    def updateDescription(self, newDescription: str) -> None:
        """Update the description of the factor."""
        self.description = newDescription 