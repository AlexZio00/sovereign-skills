"""Settings loader for the reporting service."""
import os


def get_db_host() -> str:
    return os.getenv("DB_HOST", "localhost")


def get_api_timeout_seconds() -> int:
    return int(os.getenv("API_TIMEOUT_SECONDS", "30"))
