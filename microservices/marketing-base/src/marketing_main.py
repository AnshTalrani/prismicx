"""
This module provides the main entry point for the marketing-base microservice.

MACH Principles:
 - Microservices-based design
 - API-first approach
 - Cloud-native deployment
 - Headless integration

Secure environment variable handling and error checking are demonstrated below.
"""

import os
import sys

def main():
    """
    Main execution function of marketing-base microservice.

    Raises:
        EnvironmentError: If required environment variables are not set.
    """
    required_env_var = "MARKETING_BASE_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting marketing-base microservice...")
        print(f"Using API key: {api_key[:4]}****")  # Mask sensitive data
        print("marketing-base microservice is running.")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 