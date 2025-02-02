from models.practicality import Practicality
import psycopg2
import os
import json

class PracticalityRepository:
    """Repository for managing Practicality records in PostgreSQL."""

    def __init__(self):
        """Initialize the repository with PostgreSQL connection."""
        self.conn = psycopg2.connect(os.getenv('POSTGRES_URI'))
        self.cursor = self.conn.cursor()

    def findByUserID(self, userID: str) -> Practicality:
        """Find a Practicality by userID."""
        query = "SELECT practicalityID, userID, secretSauces, factors, batchIDs FROM practicality WHERE userID=%s"
        self.cursor.execute(query, (userID,))
        result = self.cursor.fetchone()
        if result:
            practicality = Practicality(result[0], result[1])
            practicality.secretSauces = json.loads(result[2])
            practicality.factors = json.loads(result[3])
            practicality.batchIDs = result[4]
            return practicality
        return None

    def save(self, practicality: Practicality) -> None:
        """Save a Practicality record."""
        query = """
            INSERT INTO practicality (practicalityID, userID, secretSauces, factors, batchIDs)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (practicalityID) DO UPDATE
            SET secretSauces = EXCLUDED.secretSauces,
                factors = EXCLUDED.factors,
                batchIDs = EXCLUDED.batchIDs
        """
        self.cursor.execute(query, (
            practicality.practicalityID,
            practicality.userID,
            json.dumps([s.__dict__ for s in practicality.secretSauces]),
            json.dumps([f.__dict__ for f in practicality.factors]),
            practicality.batchIDs
        ))
        self.conn.commit()

    def update(self, practicality: Practicality) -> None:
        """Update an existing Practicality record."""
        self.save(practicality) 