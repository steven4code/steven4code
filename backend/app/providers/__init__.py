"""Health data provider selection."""
from __future__ import annotations

from ..config import settings
from .base import HealthProvider
from .google_health import GoogleHealthProvider
from .mock import MockProvider


def get_provider() -> HealthProvider:
    """Return the active provider based on configuration."""
    if settings.use_mock_provider:
        return MockProvider()
    return GoogleHealthProvider()


__all__ = ["HealthProvider", "get_provider", "MockProvider", "GoogleHealthProvider"]
