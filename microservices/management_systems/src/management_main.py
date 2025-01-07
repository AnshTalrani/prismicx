"""
management_systems microservice entry point.

Follows MACH architecture with secure environment variable handling.
"""

import os
import sys

def main():
    """
    Main function for the management_systems microservice.

    Raises:
        EnvironmentError: If environment variables are missing.
    """
    required_env_var = "MANAGEMENT_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting management_systems microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("management_systems microservice is running.")
    except Exception as e:
        print(f"Error in management_systems microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 