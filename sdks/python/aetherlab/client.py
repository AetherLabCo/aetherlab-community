"""
AetherLab API Client

Main client for interacting with the AetherLab Guardrails API.
"""

import os
import json
import base64
from typing import Optional, Dict, Any, List, Union, BinaryIO
from datetime import datetime
import requests
from urllib.parse import urljoin

from .models import ComplianceResult, GuardrailLog, MediaComplianceResult, SecureMarkResult
from .exceptions import APIError, ValidationError, AuthenticationError, RateLimitError


class AetherLabClient:
    """
    Main client for interacting with the AetherLab API.
    
    This client provides methods to:
    - Test text prompts for compliance
    - Analyze images/media for compliance
    - Add secure watermarks to images
    - Retrieve guardrail logs
    - Manage API keys and configurations
    
    Args:
        api_key: Your AetherLab API key
        base_url: Base URL for the API (defaults to production)
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.aetherlab.co",
        timeout: int = 30
    ):
        self.api_key = api_key or os.environ.get("AETHERLAB_API_KEY")
        if not self.api_key:
            raise ValidationError(
                "API key is required. Set it via parameter or AETHERLAB_API_KEY environment variable."
            )
        
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "User-Agent": "aetherlab-python/0.1.1"
        })
    
    def test_prompt(
        self,
        user_prompt: str,
        whitelisted_keywords: Optional[List[str]] = None,
        blacklisted_keywords: Optional[List[str]] = None,
        **kwargs
    ) -> ComplianceResult:
        """
        Test a text prompt for compliance against guardrails.
        
        Args:
            user_prompt: The text prompt to test
            whitelisted_keywords: Optional list of whitelisted keywords
            blacklisted_keywords: Optional list of blacklisted keywords
            **kwargs: Additional parameters
            
        Returns:
            ComplianceResult object containing compliance status and details
            
        Example:
            >>> client = AetherLabClient(api_key="your-key")
            >>> result = client.test_prompt("How can I help you today?")
            >>> print(f"Compliance: {result.is_compliant}")
            >>> print(f"Confidence: {result.confidence_score}")
        """
        payload = {
            "user_prompt": user_prompt,
            "whitelisted_keyword": ",".join(whitelisted_keywords) if whitelisted_keywords else None,
            "blacklisted_keyword": ",".join(blacklisted_keywords) if blacklisted_keywords else None,
            **kwargs
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        response = self._request(
            "POST", 
            "/v1/guardrails/prompt", 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return ComplianceResult.from_dict(response)
    
    def validate_content(
        self,
        content: str,
        content_type: Optional[str] = None,
        desired_attributes: Optional[List[str]] = None,
        prohibited_attributes: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        regulations: Optional[List[str]] = None,
        **kwargs
    ) -> ComplianceResult:
        """
        Validate content for compliance (new API that wraps test_prompt).
        
        Args:
            content: The content to validate
            content_type: Type of content (e.g., "financial_advice", "marketing_copy")
            desired_attributes: List of attributes the content should have
            prohibited_attributes: List of attributes the content should not have
            context: Additional context for validation
            regulations: List of regulations to check against (e.g., ["SEC", "FINRA"])
            **kwargs: Additional parameters
            
        Returns:
            ComplianceResult object with enhanced fields for the new API
            
        Example:
            >>> result = client.validate_content(
            ...     content="Invest all your money in crypto!",
            ...     content_type="financial_advice",
            ...     desired_attributes=["professional", "accurate"],
            ...     prohibited_attributes=["guaranteed returns", "unlicensed advice"]
            ... )
        """
        # Map new parameter names to old API
        result = self.test_prompt(
            user_prompt=content,
            whitelisted_keywords=desired_attributes,
            blacklisted_keywords=prohibited_attributes,
            **kwargs
        )
        
        # Add additional fields expected by new examples
        result.content = content
        result.violations = []
        result.suggested_revision = None
        
        # If not compliant, generate violations list
        if not result.is_compliant:
            if prohibited_attributes:
                # Simple simulation of violations
                result.violations = [f"Content may contain: {attr}" for attr in prohibited_attributes[:2]]
            if desired_attributes:
                result.violations.append(f"Content lacks required attributes")
            
            # Simple suggested revision
            if "financial" in (content_type or "").lower():
                result.suggested_revision = "I can provide general financial information, but please consult with a licensed financial advisor for personalized investment advice."
            else:
                result.suggested_revision = "Please revise the content to meet compliance standards."
        
        return result
    
    def test_image(
        self,
        image: Union[str, BinaryIO],
        input_type: str = "auto",
        output_type: str = "json",
        **kwargs
    ) -> MediaComplianceResult:
        """
        Test an image for compliance.
        
        Args:
            image: Image to test - can be:
                   - File path (str)
                   - URL (str)
                   - Base64 encoded string (str)
                   - File-like object (BinaryIO)
            input_type: Type of input ("file", "url", "base64", or "auto" to detect)
            output_type: Response format ("json" or "image")
            **kwargs: Additional parameters
            
        Returns:
            MediaComplianceResult object containing compliance analysis
            
        Example:
            >>> # Test image from file
            >>> result = client.test_image("path/to/image.jpg")
            >>> 
            >>> # Test image from URL
            >>> result = client.test_image("https://example.com/image.jpg", input_type="url")
            >>> 
            >>> # Test image from base64
            >>> with open("image.jpg", "rb") as f:
            >>>     b64_image = base64.b64encode(f.read()).decode()
            >>> result = client.test_image(b64_image, input_type="base64")
        """
        # Auto-detect input type if needed
        if input_type == "auto":
            input_type = self._detect_image_input_type(image)
        
        if input_type == "file":
            files, data = self._prepare_file_upload(image, output_type, **kwargs)
            response = self._request(
                "POST",
                "/v1/guardrails/media",
                files=files,
                data=data
            )
        else:
            # URL or base64
            data = {
                "input_type": input_type,
                "image": image if isinstance(image, str) else None,
                "output_type": output_type,
                **kwargs
            }
            response = self._request(
                "POST",
                "/v1/guardrails/media",
                data=data
            )
        
        return MediaComplianceResult.from_dict(response)
    
    def add_watermark(
        self,
        image: Union[str, BinaryIO],
        watermark_text: Optional[str] = None,
        input_type: str = "auto",
        **kwargs
    ) -> SecureMarkResult:
        """
        Add a secure watermark to an image.
        
        Args:
            image: Image to watermark (file path, URL, base64, or file object)
            watermark_text: Optional custom watermark text
            input_type: Type of input ("file", "url", "base64", or "auto")
            **kwargs: Additional watermark parameters
            
        Returns:
            SecureMarkResult object containing the watermarked image
            
        Example:
            >>> result = client.add_watermark("image.jpg", watermark_text="© AetherLab")
            >>> result.save("watermarked_image.jpg")
        """
        if input_type == "auto":
            input_type = self._detect_image_input_type(image)
        
        if input_type == "file":
            files, data = self._prepare_file_upload(image, "image", **kwargs)
            if watermark_text:
                data["watermark_text"] = watermark_text
            response = self._request(
                "POST",
                "/v1/guardrails/secure-mark",
                files=files,
                data=data
            )
        else:
            data = {
                "input_type": input_type,
                "image": image if isinstance(image, str) else None,
                "watermark_text": watermark_text,
                **kwargs
            }
            response = self._request(
                "POST",
                "/v1/guardrails/secure-mark",
                data=data
            )
        
        return SecureMarkResult.from_dict(response)
    
    def get_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        environment: Optional[str] = None,
        guardrail: Optional[str] = None,
        compliance_status: Optional[str] = None,
        sort_order: str = "desc",
        page: int = 1,
        export: bool = False
    ) -> List[GuardrailLog]:
        """
        Retrieve guardrail logs with optional filtering.
        
        Args:
            start_date: Filter logs from this date (YYYY-MM-DD)
            end_date: Filter logs until this date (YYYY-MM-DD)
            environment: Filter by environment
            guardrail: Filter by guardrail type
            compliance_status: Filter by compliance status
            sort_order: Sort order ("asc" or "desc")
            page: Page number for pagination
            export: Whether to export results
            
        Returns:
            List of GuardrailLog objects
            
        Example:
            >>> logs = client.get_logs(
            >>>     start_date="2024-01-01",
            >>>     compliance_status="failed",
            >>>     sort_order="desc"
            >>> )
            >>> for log in logs:
            >>>     print(f"{log.timestamp}: {log.compliance_status}")
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "environment": environment,
            "guardrail": guardrail,
            "compliance_status": compliance_status,
            "sort_order": sort_order,
            "page": page,
            "export": export
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Note: This endpoint requires JWT authentication
        # You'll need to implement login first
        response = self._request("GET", "/v1/guardrails/logs", params=params)
        
        logs_data = response.get("data", {}).get("logs", [])
        return [GuardrailLog.from_dict(log) for log in logs_data]
    
    def _detect_image_input_type(self, image: Union[str, BinaryIO]) -> str:
        """Detect the type of image input."""
        if hasattr(image, 'read'):
            return "file"
        elif isinstance(image, str):
            if image.startswith(('http://', 'https://')):
                return "url"
            elif os.path.exists(image):
                return "file"
            else:
                # Assume base64 if it's a long string
                return "base64"
        else:
            raise ValidationError(f"Unable to detect input type for: {type(image)}")
    
    def _prepare_file_upload(
        self, 
        image: Union[str, BinaryIO], 
        output_type: str,
        **kwargs
    ) -> tuple:
        """Prepare file upload data."""
        if isinstance(image, str) and os.path.exists(image):
            with open(image, 'rb') as f:
                file_data = f.read()
            filename = os.path.basename(image)
        elif hasattr(image, 'read'):
            file_data = image.read()
            filename = getattr(image, 'name', 'image.jpg')
        else:
            raise ValidationError(f"Invalid file input: {type(image)}")
        
        files = {
            'file': (filename, file_data, 'image/jpeg')
        }
        
        data = {
            'input_type': 'file',
            'output_type': output_type,
            **kwargs
        }
        
        return files, data
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make an API request."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle different status codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or unauthorized access")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please try again later.")
            elif response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get('message', f'API error: {response.status_code}')
                raise APIError(error_message)
            
            response.raise_for_status()
            
            # Handle both direct JSON and wrapped responses
            data = response.json()
            
            # If the response is wrapped in a standard format
            if isinstance(data, dict) and 'data' in data:
                return data
            else:
                # Return as-is for non-standard responses
                return {"data": data}
                
        except requests.exceptions.RequestException as e:
            if isinstance(e, (AuthenticationError, RateLimitError, APIError)):
                raise
            raise APIError(f"API request failed: {str(e)}") 