"""
Customer-support-bot microservice main entry point.

Demonstrates MACH principles and environment variable security checks.
"""

import os
import sys

def main():
    """
    Main function for the customer-support-bot microservice.

    Raises:
        EnvironmentError: If needed environment variables are not set.
    """
    required_env_var = "CS_BOT_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )
    
    try:
        print("Starting customer-support-bot microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("Customer-support-bot microservice is running.")
    except Exception as e:
        print(f"Error in customer-support-bot microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 