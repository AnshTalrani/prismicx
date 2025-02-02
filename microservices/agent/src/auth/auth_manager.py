from datetime import datetime, timedelta
from typing import Optional
from ..models.token import JWT, TokenPayload
import jwt

class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.key_rotation_schedule: datetime = datetime.utcnow() + timedelta(days=30)  # Example rotation schedule

    def generate_token(self, service: str) -> str:
        """
        Generates a JWT token for the specified service.
        """
        token = jwt.encode(
            {"service": service, "exp": datetime.utcnow() + timedelta(hours=1)},
            self.secret_key,
            algorithm="HS256"
        )
        return token

    # Removed additional methods to align strictly with the plan 