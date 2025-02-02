from typing import List
from .secret_sauce import SecretSauce
from .factor import Factor

class Practicality:
    """
    Represents the practicality details for a user.

    Attributes:
        practicalityID (str): Primary key identifier.
        userID (str): Foreign key linking to the user.
        secretSauces (List[SecretSauce]): List of secret sauces.
        factors (List[Factor]): List of factors.
        batchIDs (List[str]): List of batch identifiers.
    """

    def __init__(self, practicalityID: str, userID: str):
        self.practicalityID = practicalityID
        self.userID = userID
        self.secretSauces: List[SecretSauce] = []
        self.factors: List[Factor] = []
        self.batchIDs: List[str] = []

    def getSecretSauces(self) -> List[SecretSauce]:
        """Retrieve the list of secret sauces."""
        return self.secretSauces

    def addFactor(self, factor: Factor) -> None:
        """Add a factor."""
        self.factors.append(factor)

    def removeFactor(self, factorID: str) -> None:
        """Remove a factor by its ID."""
        self.factors = [f for f in self.factors if f.factorID != factorID]

    def updateSecretSauces(self, newSecretSauces: List[SecretSauce]) -> None:
        """Update the list of secret sauces."""
        self.secretSauces = newSecretSauces 