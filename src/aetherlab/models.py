"""Response models for the AetherLab SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["ComplianceResult", "MediaComplianceResult"]


def _data_of(response: dict[str, Any]) -> dict[str, Any]:
    """Return the ``data`` object of an API envelope, tolerating a flat dict."""
    data = response.get("data")
    if isinstance(data, dict):
        return data
    return response


@dataclass
class ComplianceResult:
    """Result of a prompt guardrail check (``POST /v1/guardrails/prompt``).

    Every field is taken verbatim from the API response; nothing is computed
    client-side except :attr:`is_compliant`, which is derived from
    :attr:`compliance_status`.

    Attributes:
        compliance_status: ``"Compliant"`` or ``"Non-Compliant"`` as returned
            by the API.
        is_compliant: ``True`` when ``compliance_status`` equals
            ``"Compliant"`` (case-insensitive).
        avg_threat_level: Average threat level in ``[0.0, 1.0]``; higher means
            more likely to violate the configured policies.
        confidence: The model's confidence in the verdict, in ``[0.0, 1.0]``,
            exactly as returned by the API.
        rationale: Free-text explanation of the verdict; may be ``None``.
        raw: The complete, unmodified JSON response body.
    """

    compliance_status: str
    avg_threat_level: float | None
    confidence: float | None
    rationale: str | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def is_compliant(self) -> bool:
        return self.compliance_status.strip().lower() == "compliant"

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> ComplianceResult:
        data = _data_of(response)
        return cls(
            compliance_status=str(data.get("compliance_status", "")),
            avg_threat_level=data.get("avg_threat_level"),
            confidence=data.get("confidence"),
            rationale=data.get("rationale"),
            raw=response,
        )


@dataclass
class MediaComplianceResult(ComplianceResult):
    """Result of a media guardrail check (``POST /v1/guardrails/media``).

    Same fields as :class:`ComplianceResult`; the API returns the identical
    ``data`` shape for media checks.
    """

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> MediaComplianceResult:
        data = _data_of(response)
        return cls(
            compliance_status=str(data.get("compliance_status", "")),
            avg_threat_level=data.get("avg_threat_level"),
            confidence=data.get("confidence"),
            rationale=data.get("rationale"),
            raw=response,
        )
