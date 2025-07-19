#!/bin/bash

# Create directory structure
mkdir -p sdks/python/aetherlab
mkdir -p examples/python
mkdir -p docs

# Create __init__.py
cat > sdks/python/aetherlab/__init__.py << 'PYEOF'
"""
AetherLab Python SDK

The official Python SDK for AetherLab's AI Guardrails and Compliance Platform.
"""

__version__ = "0.1.0"

from .client import AetherLabClient
from .exceptions import (
    AetherLabError, 
    APIError, 
    ValidationError,
    AuthenticationError,
    RateLimitError
)
from .models import (
    ComplianceResult,
    GuardrailLog,
    MediaComplianceResult,
    SecureMarkResult
)

__all__ = [
    "AetherLabClient",
    "AetherLabError",
    "APIError", 
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "ComplianceResult",
    "GuardrailLog",
    "MediaComplianceResult",
    "SecureMarkResult",
]
PYEOF

echo "SDK files created successfully!"
