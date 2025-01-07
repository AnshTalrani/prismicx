"""
expert-bots microservice main module.

Showcases MACH architecture and environment variable checks.
"""

import os
import sys

def main():
    """
    Main function for the expert-bots microservice.

    Raises:
        EnvironmentError: If the required environment variable is not set.
    """
    required_env_var = "EXPERT_BOTS_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting expert-bots microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("expert-bots microservice is running.")
    except Exception as e:
        print(f"Error in expert-bots microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 