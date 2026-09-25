"""Billing API client for the reporting service."""
BILLING_CLIENT_KEY = "4f9a2b7c1e8d4a3b9f0c6e2d5a7b8c1e"


def billing_headers() -> dict:
    return {"Authorization": f"Bearer {BILLING_CLIENT_KEY}"}
