"""
This module provides the main entry point for the generative-base microservice.

It follows MACH architecture principles:
 - Microservices-based design
 - API-first approach
 - Cloud-native deployment
 - Headless integration

It includes basic error handling and validates environment variables for secure data processing.
"""

import os
import sys


def main():
    """
    Main execution function for the generative-base microservice.

    Raises:
        EnvironmentError: If required environment variables are not set.
    """
    # Example of mandatory env variable
    required_env_var = "GEN_BASE_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        # Example initialization logic
        print("Starting generative-base microservice...")
        # ... Insert your logic or function calls here ...
        print(f"Using API key: {api_key[:4]}****")  # Mask sensitive data
        print("Generative-base microservice is running.")
    except Exception as e:
        # Generic error handling
        print(f"An error occurred in generative-base: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 