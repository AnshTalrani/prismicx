"""
This module provides the main entry point for the agent microservice.

It demonstrates secure handling of environment variables following MACH principles.
"""

import os
import sys

def main():
    """
    Main entry point for the agent microservice.

    Raises:
        EnvironmentError: If a required environment variable is missing.
    """
    required_env_var = "AGENT_API_KEY"
    api_key = os.getenv(required_env_var)

    if not api_key:
        raise EnvironmentError(
            f"The required environment variable '{required_env_var}' is not set."
        )

    try:
        print("Starting agent microservice...")
        print(f"Using API key: {api_key[:4]}****")
        print("Agent microservice is running.")
    except Exception as e:
        print(f"Error in agent microservice: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 