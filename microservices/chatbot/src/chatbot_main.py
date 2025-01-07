"""
This module serves as the main entry point for the chatbot microservice.

In line with MACH principles, environment variables are used securely.
"""

import os
import sys

def main():
    """
    Main function for chatbot microservice.

    Raises:
        EnvironmentError: If environment variable is missing.
    """
    required_env_var = "CHATBOT_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting chatbot microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("Chatbot microservice is running.")
    except Exception as e:
        print(f"Error in chatbot microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 