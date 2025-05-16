"""
mlops-pipeline microservice entry point.

Demonstrates environment variable handling in line with MACH principles.
"""

import os
import sys

def main():
    """
    Main function for the mlops-pipeline microservice.

    Raises:
        EnvironmentError: If environment variables aren't set.
    """
    required_env_var = "MLOPS_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting mlops-pipeline microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("mlops-pipeline microservice is running.")
    except Exception as e:
        print(f"Error in mlops-pipeline microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 