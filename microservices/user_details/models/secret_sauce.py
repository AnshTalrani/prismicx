class SecretSauce:
    """
    Represents a secret sauce.

    Attributes:
        sauceID (str): Identifier for the sauce.
        description (str): Description of the sauce.
        layerID (str): Associated layer identifier.
    """

    def __init__(self, sauceID: str, description: str, layerID: str):
        self.sauceID = sauceID
        self.description = description
        self.layerID = layerID

    def updateDescription(self, newDescription: str) -> None:
        """Update the description of the secret sauce."""
        self.description = newDescription 