"""
Database configuration package.

This package provides configuration settings for database connections,
supporting the multi-tenant architecture described in the project documentation.
"""

from .postgres_config import PostgresSettings, PostgresConfig, postgres_config

__all__ = ["PostgresSettings", "PostgresConfig", "postgres_config"] 