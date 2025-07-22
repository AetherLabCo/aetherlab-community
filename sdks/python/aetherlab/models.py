"""
AetherLab SDK Data Models

Data models for API responses and requests.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import base64
import json


@dataclass
class ComplianceResult:
    """Results from a text prompt compliance check."""
    
    status: int
    message: str
    is_compliant: bool
    confidence_score: float
    avg_threat_level: float
    guardrails_triggered: List[str]
    details: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]
    
    # Additional fields for new API compatibility
    content: Optional[str] = None
    content_type: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    violations: Optional[List[str]] = None
    suggested_revision: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComplianceResult":
        """Create ComplianceResult from API response."""
        response_data = data.get("data", {})
        
        # Parse compliance status
        compliance_status = response_data.get("compliance_status", "Compliant")
        is_compliant = compliance_status.lower() == "compliant"
        
        # Extract guardrails triggered
        guardrails = []
        if "triggered_guardrails" in response_data:
            guardrails = response_data["triggered_guardrails"]
        elif "guardrails" in response_data:
            guardrails = [g for g, triggered in response_data["guardrails"].items() if triggered]
        
        # Get threat level and convert to confidence score
        # Lower threat level = higher confidence in compliance
        avg_threat_level = response_data.get("avg_threat_level", 0.0)
        confidence_score = 1.0 - avg_threat_level
        
        return cls(
            status=data.get("status", 200),
            message=data.get("message", ""),
            is_compliant=is_compliant,
            confidence_score=confidence_score,
            avg_threat_level=avg_threat_level,
            guardrails_triggered=guardrails,
            details=response_data.get("details", {}),
            recommendations=response_data.get("recommendations", []),
            metadata=response_data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """String representation of compliance result."""
        status = "✅ COMPLIANT" if self.is_compliant else "❌ NON-COMPLIANT"
        return (
            f"{status}\n"
            f"Confidence: {self.confidence_score:.2%}\n"
            f"Guardrails Triggered: {', '.join(self.guardrails_triggered) if self.guardrails_triggered else 'None'}"
        )


@dataclass
class MediaComplianceResult:
    """Results from image/media compliance check."""
    
    status: int
    message: str
    is_compliant: bool
    confidence_score: float
    detected_objects: List[Dict[str, Any]]
    detected_text: Optional[str]
    content_warnings: List[str]
    metadata: Dict[str, Any]
    output_image: Optional[str]  # Base64 encoded if output_type was "image"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaComplianceResult":
        """Create MediaComplianceResult from API response."""
        response_data = data.get("data", {})
        
        return cls(
            status=data.get("status", 200),
            message=data.get("message", ""),
            is_compliant=response_data.get("is_compliant", True),
            confidence_score=response_data.get("confidence_score", 1.0),
            detected_objects=response_data.get("detected_objects", []),
            detected_text=response_data.get("detected_text"),
            content_warnings=response_data.get("content_warnings", []),
            metadata=response_data.get("metadata", {}),
            output_image=response_data.get("output_image")
        )
    
    def save_output_image(self, filepath: str) -> None:
        """Save the output image if available."""
        if self.output_image:
            image_data = base64.b64decode(self.output_image)
            with open(filepath, 'wb') as f:
                f.write(image_data)


@dataclass
class SecureMarkResult:
    """Results from secure watermark operation."""
    
    status: int
    message: str
    success: bool
    watermarked_image: str  # Base64 encoded
    watermark_id: Optional[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecureMarkResult":
        """Create SecureMarkResult from API response."""
        # Handle raw image response
        if isinstance(data, bytes):
            return cls(
                status=200,
                message="Watermark applied successfully",
                success=True,
                watermarked_image=base64.b64encode(data).decode(),
                watermark_id=None,
                metadata={}
            )
        
        response_data = data.get("data", {})
        
        return cls(
            status=data.get("status", 200),
            message=data.get("message", ""),
            success=data.get("status", 200) == 200,
            watermarked_image=response_data.get("watermarked_image", ""),
            watermark_id=response_data.get("watermark_id"),
            metadata=response_data.get("metadata", {})
        )
    
    def save(self, filepath: str) -> None:
        """Save the watermarked image to a file."""
        if self.watermarked_image:
            image_data = base64.b64decode(self.watermarked_image)
            with open(filepath, 'wb') as f:
                f.write(image_data)


@dataclass
class GuardrailLog:
    """A log entry from the guardrail system."""
    
    id: str
    timestamp: datetime
    user_id: Optional[str]
    company_id: str
    environment: str
    guardrail_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    compliance_status: str
    confidence_score: float
    processing_time_ms: int
    metadata: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuardrailLog":
        """Create GuardrailLog from API response."""
        # Parse timestamp
        timestamp_str = data.get("timestamp", data.get("created_at", ""))
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        return cls(
            id=data.get("id", ""),
            timestamp=timestamp,
            user_id=data.get("user_id"),
            company_id=data.get("company_id", ""),
            environment=data.get("environment", ""),
            guardrail_type=data.get("guardrail_type", data.get("guardrail", "")),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data", {}),
            compliance_status=data.get("compliance_status", ""),
            confidence_score=data.get("confidence_score", 0.0),
            processing_time_ms=data.get("processing_time_ms", 0),
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        """Convert log to JSON string."""
        data = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "company_id": self.company_id,
            "environment": self.environment,
            "guardrail_type": self.guardrail_type,
            "compliance_status": self.compliance_status,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms
        }
        return json.dumps(data, indent=2) 