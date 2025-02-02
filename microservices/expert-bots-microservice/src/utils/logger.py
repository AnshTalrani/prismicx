"""
Logger utility for logging activities and errors.
"""

import logging

class Logger:
    def __init__(self):
        """
        Initializes the Logger with predefined settings.
        """
        self.logger = logging.getLogger("expert_bots_logger")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_activity(self, activity: str) -> None:
        """
        Logs an activity message.

        Args:
            activity (str): Activity description to log.
        """
        self.logger.info(activity)

    def log_error(self, error: str) -> None:
        """
        Logs an error message.

        Args:
            error (str): Error description to log.
        """
        self.logger.error(error) 