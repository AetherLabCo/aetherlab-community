# Security Best Practices for AetherLab Integration

This guide covers security best practices when integrating AetherLab into your applications.

## API Key Management

### Never Hardcode API Keys

❌ **Bad Practice:**
```python
client = AetherLabClient(api_key="al_prod_2f6fb1ed9dcb...")
```

✅ **Good Practice:**
```python
import os
client = AetherLabClient(api_key=os.environ.get("AETHERLAB_API_KEY"))
```

### Use Environment Variables

Set your API key as an environment variable:

```bash
# .env file (add to .gitignore!)
AETHERLAB_API_KEY=your-api-key-here

# Or export in shell
export AETHERLAB_API_KEY="your-api-key-here"
```

### Use Secrets Management

For production applications, use proper secrets management:

- **AWS**: AWS Secrets Manager or Parameter Store
- **Azure**: Azure Key Vault
- **Google Cloud**: Secret Manager
- **Kubernetes**: Kubernetes Secrets
- **HashiCorp Vault**: For multi-cloud environments

Example with AWS Secrets Manager:

```python
import boto3
import json
from aetherlab import AetherLabClient

def get_api_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='aetherlab-api-key')
    secret = json.loads(response['SecretString'])
    return secret['api_key']

aetherlab_client = AetherLabClient(api_key=get_api_key())
```

## Input Validation

### Always Validate User Input

Don't trust any user input, even after AetherLab checks:

```python
def process_user_input(user_input):
    # Basic validation first
    if not user_input or len(user_input) > 10000:
        return "Invalid input"
    
    # Remove any potential injection attempts
    cleaned_input = user_input.strip()
    
    # Then check with AetherLab
    result = client.test_prompt(cleaned_input)
    
    if not result.is_compliant:
        return "Input violates content policy"
    
    # Process the validated input
    return process_safe_input(cleaned_input)
```

### Implement Defense in Depth

Layer multiple security checks:

```python
class SecureContentProcessor:
    def __init__(self):
        self.aetherlab = AetherLabClient()
        self.max_length = 5000
        self.rate_limiter = RateLimiter()
        
    def process(self, content, user_id):
        # Layer 1: Rate limiting
        if not self.rate_limiter.check(user_id):
            raise RateLimitExceeded()
        
        # Layer 2: Input validation
        if len(content) > self.max_length:
            raise ValidationError("Content too long")
        
        # Layer 3: Content filtering
        result = self.aetherlab.test_prompt(content)
        if not result.is_compliant:
            raise ContentPolicyViolation()
        
        # Layer 4: Output sanitization
        processed = self.sanitize_output(content)
        
        return processed
```

## Error Handling

### Don't Expose Internal Errors

❌ **Bad Practice:**
```python
try:
    result = client.test_prompt(user_input)
except Exception as e:
    return f"Error: {str(e)}"  # Exposes internal details
```

✅ **Good Practice:**
```python
try:
    result = client.test_prompt(user_input)
except AuthenticationError:
    logger.error("Authentication failed")
    return "Service temporarily unavailable"
except APIError:
    logger.error("API error occurred")
    return "Unable to process request"
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return "An error occurred"
```

### Implement Proper Logging

Log security events without exposing sensitive data:

```python
import logging
import hashlib

logger = logging.getLogger(__name__)

def log_security_event(user_id, action, result):
    # Hash sensitive data
    user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    logger.info({
        'event': 'security_check',
        'user_hash': user_hash,
        'action': action,
        'result': result,
        'timestamp': datetime.utcnow().isoformat()
    })
```

## Rate Limiting

### Implement Client-Side Rate Limiting

Protect your API quota and prevent abuse:

```python
from functools import wraps
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=60, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
    
    def check(self):
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            return False
        
        self.requests.append(now)
        return True

def rate_limited(limiter):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.check():
                raise RateLimitExceeded("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
limiter = RateLimiter(max_requests=100, window_seconds=60)

@rate_limited(limiter)
def check_content(content):
    return client.test_prompt(content)
```

## Secure Communication

### Always Use HTTPS

The AetherLab SDK uses HTTPS by default. Never disable SSL verification:

```python
# ❌ NEVER DO THIS
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# ✅ The SDK handles HTTPS properly by default
client = AetherLabClient()
```

### Implement Request Signing (if available)

For additional security, implement request signing:

```python
import hmac
import hashlib
import time

def sign_request(payload, secret):
    timestamp = str(int(time.time()))
    message = f"{timestamp}.{json.dumps(payload)}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature, timestamp
```

## Data Privacy

### Don't Log Sensitive Content

```python
def process_private_content(content, user_id):
    # Don't log the actual content
    logger.info(f"Processing content for user {user_id}, length: {len(content)}")
    
    result = client.test_prompt(content)
    
    # Log only the result, not the content
    logger.info(f"Content check result: {result.is_compliant}")
    
    return result
```

### Implement Data Retention Policies

```python
class ComplianceLogger:
    def __init__(self, retention_days=30):
        self.retention_days = retention_days
    
    def log_check(self, user_id, result, content_hash):
        # Store only necessary data
        record = {
            'timestamp': datetime.utcnow(),
            'user_id': user_id,
            'content_hash': content_hash,  # Not the actual content
            'is_compliant': result.is_compliant,
            'threat_level': result.avg_threat_level
        }
        
        # Store with TTL for automatic deletion
        self.store_with_ttl(record, self.retention_days)
```

## Authentication & Authorization

### Implement Proper Access Controls

```python
from functools import wraps
from flask import request, abort

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key or not validate_api_key(api_key):
            abort(401)
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/check-content', methods=['POST'])
@require_api_key
def check_content():
    # Only authenticated users can access
    pass
```

### Use Role-Based Access Control

```python
class ContentModerator:
    def __init__(self, user_role):
        self.user_role = user_role
        self.client = AetherLabClient()
    
    def can_override_safety(self):
        return self.user_role in ['admin', 'senior_moderator']
    
    def check_content(self, content):
        result = self.client.test_prompt(content)
        
        if not result.is_compliant and not self.can_override_safety():
            raise PermissionError("Cannot override safety check")
        
        return result
```

## Monitoring & Alerting

### Set Up Security Monitoring

```python
class SecurityMonitor:
    def __init__(self):
        self.alert_threshold = 0.8
        self.failed_attempts = defaultdict(int)
    
    def check_and_alert(self, user_id, result):
        if result.avg_threat_level > self.alert_threshold:
            self.send_alert(f"High threat content from user {user_id}")
        
        if not result.is_compliant:
            self.failed_attempts[user_id] += 1
            
            if self.failed_attempts[user_id] > 5:
                self.send_alert(f"Multiple violations from user {user_id}")
                self.block_user(user_id)
```

## Testing Security

### Write Security Tests

```python
import pytest
from unittest.mock import patch

class TestSecurityFeatures:
    def test_api_key_not_exposed(self):
        """Ensure API key is not logged or exposed."""
        with patch('logging.Logger.info') as mock_log:
            client = AetherLabClient()
            client.test_prompt("test")
            
            # Check logs don't contain API key
            for call in mock_log.call_args_list:
                assert "al_prod" not in str(call)
    
    def test_rate_limiting(self):
        """Test rate limiting works correctly."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        assert limiter.check() == True
        assert limiter.check() == True
        assert limiter.check() == False  # Should be rate limited
    
    def test_input_validation(self):
        """Test input validation."""
        processor = SecureContentProcessor()
        
        # Test oversized input
        with pytest.raises(ValidationError):
            processor.process("x" * 10001, "user123")
```

## Security Checklist

Before deploying to production, ensure:

- [ ] API keys are stored securely (not in code)
- [ ] All user inputs are validated
- [ ] Errors don't expose internal details
- [ ] Rate limiting is implemented
- [ ] HTTPS is used for all communications
- [ ] Sensitive data is not logged
- [ ] Access controls are in place
- [ ] Security monitoring is active
- [ ] Regular security audits are scheduled
- [ ] Incident response plan exists

## Incident Response

### Have a Plan

1. **Detection**: Monitor for anomalies
2. **Containment**: Isolate affected systems
3. **Investigation**: Determine scope and cause
4. **Remediation**: Fix vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Update procedures

### Example Incident Response

```python
class IncidentResponder:
    def handle_security_incident(self, incident_type, details):
        # 1. Log the incident
        self.log_incident(incident_type, details)
        
        # 2. Immediate containment
        if incident_type == "api_key_compromise":
            self.rotate_api_keys()
        elif incident_type == "abuse_detected":
            self.block_abusive_users(details['user_ids'])
        
        # 3. Notify stakeholders
        self.send_notifications(incident_type, details)
        
        # 4. Collect forensics
        self.collect_logs(details['timeframe'])
        
        # 5. Remediate
        self.apply_fixes(incident_type)
```

## Conclusion

Security is not a one-time implementation but an ongoing process. Regularly review and update your security measures, stay informed about new threats, and always follow the principle of least privilege.

For security concerns or to report vulnerabilities, contact: security@aetherlab.ai 