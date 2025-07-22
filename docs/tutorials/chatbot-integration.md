# Tutorial: Integrating AetherLab with Your Chatbot

This tutorial shows how to integrate AetherLab's guardrails into your chatbot application to ensure safe and compliant AI interactions.

## Prerequisites

- Python 3.8+
- AetherLab SDK installed
- An AetherLab API key

## Building a Safe Chatbot

### Step 1: Basic Setup

First, let's create a simple chatbot class that uses AetherLab for safety checks:

```python
from aetherlab import AetherLabClient
from aetherlab.exceptions import APIError
import os

class SafeChatbot:
    def __init__(self):
        # Initialize AetherLab client
        self.aetherlab = AetherLabClient(
            api_key=os.environ.get("AETHERLAB_API_KEY")
        )
        
        # Define safety thresholds
        self.max_threat_level = 0.3
        self.min_confidence = 0.7
        
        # Define content policies
        self.blacklisted_terms = [
            "harmful", "illegal", "dangerous", 
            "exploit", "hack", "abuse"
        ]
        
    def is_input_safe(self, user_input):
        """Check if user input is safe to process."""
        try:
            result = self.aetherlab.test_prompt(
                user_input,
                blacklisted_keywords=self.blacklisted_terms
            )
            
            return (
                result.is_compliant and 
                result.avg_threat_level < self.max_threat_level and
                result.confidence_score > self.min_confidence
            )
        except APIError:
            # If API fails, err on the side of caution
            return False
    
    def is_response_safe(self, ai_response):
        """Check if AI response is safe to send."""
        try:
            result = self.aetherlab.test_prompt(ai_response)
            
            return (
                result.is_compliant and 
                result.avg_threat_level < self.max_threat_level
            )
        except APIError:
            return False
    
    def process_message(self, user_input):
        """Process a user message with safety checks."""
        # Check input safety
        if not self.is_input_safe(user_input):
            return "I'm sorry, but I cannot process that request."
        
        # Generate AI response (placeholder - use your AI model here)
        ai_response = self.generate_response(user_input)
        
        # Check response safety
        if not self.is_response_safe(ai_response):
            return "I apologize, but I cannot provide that information."
        
        return ai_response
    
    def generate_response(self, user_input):
        """Generate AI response - replace with your AI model."""
        # This is a placeholder - integrate your AI model here
        return f"You said: {user_input}"
```

### Step 2: Adding Context-Aware Filtering

Let's enhance our chatbot with context-aware filtering:

```python
class ContextAwareChatbot(SafeChatbot):
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.user_profile = {}
        
    def check_context_safety(self, user_input):
        """Check safety considering conversation context."""
        # Combine current input with recent history
        context = " ".join(self.conversation_history[-3:]) + " " + user_input
        
        # Check for manipulation attempts
        manipulation_keywords = ["ignore previous", "forget instructions", "new rules"]
        
        result = self.aetherlab.test_prompt(
            context,
            blacklisted_keywords=self.blacklisted_terms + manipulation_keywords
        )
        
        return result.is_compliant
    
    def process_message(self, user_input, user_id=None):
        """Process message with context awareness."""
        # Check context safety
        if not self.check_context_safety(user_input):
            return "I notice you're trying to change our conversation rules. Let's stay on topic."
        
        # Regular safety check
        if not self.is_input_safe(user_input):
            return "I'm sorry, but I cannot process that request."
        
        # Generate and check response
        ai_response = self.generate_response(user_input)
        
        if not self.is_response_safe(ai_response):
            return "I apologize, but I cannot provide that information."
        
        # Update conversation history
        self.conversation_history.append(user_input)
        self.conversation_history.append(ai_response)
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return ai_response
```

### Step 3: Implementing Rate Limiting and Caching

Add rate limiting and caching for better performance:

```python
import time
from functools import lru_cache
import hashlib

class OptimizedChatbot(ContextAwareChatbot):
    def __init__(self):
        super().__init__()
        self.request_times = []
        self.max_requests_per_minute = 50
        
    def check_rate_limit(self):
        """Check if we're within rate limits."""
        current_time = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            return False
        
        self.request_times.append(current_time)
        return True
    
    @lru_cache(maxsize=1000)
    def cached_safety_check(self, text_hash):
        """Cached safety check to reduce API calls."""
        # Note: In production, you'd retrieve the actual text from a secure store
        # This is simplified for the example
        return self.is_input_safe(text_hash)
    
    def process_message(self, user_input, user_id=None):
        """Process message with optimization."""
        # Check rate limit
        if not self.check_rate_limit():
            return "Please slow down. Try again in a moment."
        
        # Hash the input for caching (in production, use a more secure approach)
        input_hash = hashlib.sha256(user_input.encode()).hexdigest()
        
        # Use cached result if available
        if not self.cached_safety_check(input_hash):
            return "I'm sorry, but I cannot process that request."
        
        # Continue with normal processing
        return super().process_message(user_input, user_id)
```

### Step 4: Creating a Complete Application

Here's a complete example with a simple CLI interface:

```python
import asyncio
from datetime import datetime

class ChatbotApp:
    def __init__(self):
        self.chatbot = OptimizedChatbot()
        self.sessions = {}
        
    def start_session(self, user_id):
        """Start a new chat session."""
        self.sessions[user_id] = {
            'start_time': datetime.now(),
            'message_count': 0
        }
        
    def end_session(self, user_id):
        """End a chat session."""
        if user_id in self.sessions:
            session = self.sessions[user_id]
            duration = datetime.now() - session['start_time']
            print(f"Session ended. Duration: {duration}, Messages: {session['message_count']}")
            del self.sessions[user_id]
    
    async def handle_message(self, user_id, message):
        """Handle a user message asynchronously."""
        if user_id not in self.sessions:
            self.start_session(user_id)
        
        self.sessions[user_id]['message_count'] += 1
        
        # Process message
        response = self.chatbot.process_message(message, user_id)
        
        return response
    
    def run_cli(self):
        """Run a simple CLI interface."""
        print("Welcome to SafeChat! Type 'quit' to exit.")
        print("-" * 50)
        
        user_id = "cli_user"
        self.start_session(user_id)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                
                # Run async handler in sync context
                response = asyncio.run(self.handle_message(user_id, user_input))
                print(f"Bot: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.end_session(user_id)
        print("\nGoodbye!")

# Run the application
if __name__ == "__main__":
    app = ChatbotApp()
    app.run_cli()
```

### Step 5: Advanced Features

#### Custom Guardrails

Create domain-specific guardrails:

```python
class MedicalChatbot(OptimizedChatbot):
    def __init__(self):
        super().__init__()
        # Medical-specific blacklisted terms
        self.blacklisted_terms.extend([
            "diagnose", "prescribe", "medication", "treatment"
        ])
        
        # Medical disclaimer
        self.disclaimer = (
            "I'm an AI assistant and cannot provide medical advice. "
            "Please consult a healthcare professional."
        )
    
    def process_message(self, user_input, user_id=None):
        """Process with medical safety checks."""
        # Check for medical advice requests
        medical_terms = ["symptoms", "disease", "medicine", "doctor"]
        
        result = self.aetherlab.test_prompt(
            user_input,
            blacklisted_keywords=medical_terms
        )
        
        if not result.is_compliant:
            return self.disclaimer
        
        return super().process_message(user_input, user_id)
```

#### Logging and Monitoring

Add comprehensive logging:

```python
import logging
from datetime import datetime

class MonitoredChatbot(OptimizedChatbot):
    def __init__(self):
        super().__init__()
        # Set up logging
        logging.basicConfig(
            filename='chatbot_safety.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def log_safety_event(self, user_id, input_text, result):
        """Log safety check events."""
        self.logger.info(f"Safety check for user {user_id}")
        self.logger.info(f"Input: {input_text[:100]}...")
        self.logger.info(f"Compliant: {result.is_compliant}")
        self.logger.info(f"Threat level: {result.avg_threat_level}")
        
        if not result.is_compliant:
            self.logger.warning(f"Non-compliant input from user {user_id}")
    
    def process_message(self, user_input, user_id=None):
        """Process with monitoring."""
        # Perform safety check with logging
        result = self.aetherlab.test_prompt(
            user_input,
            blacklisted_keywords=self.blacklisted_terms
        )
        
        self.log_safety_event(user_id or "unknown", user_input, result)
        
        if not result.is_compliant:
            return "I'm sorry, but I cannot process that request."
        
        return super().process_message(user_input, user_id)
```

## Best Practices

1. **Always check both inputs and outputs** - Don't trust user input or AI responses
2. **Implement fallback responses** - Have safe default responses when checks fail
3. **Log safety events** - Track patterns and improve your guardrails
4. **Use caching wisely** - Cache safety checks for common inputs
5. **Handle API failures gracefully** - Don't expose errors to users
6. **Update guardrails regularly** - Adapt to new threats and use cases

## Testing Your Integration

Here's a test suite for your chatbot:

```python
import unittest
from unittest.mock import Mock, patch

class TestSafeChatbot(unittest.TestCase):
    def setUp(self):
        self.chatbot = SafeChatbot()
    
    def test_safe_input(self):
        """Test that safe inputs are processed."""
        response = self.chatbot.process_message("What's the weather today?")
        self.assertNotIn("cannot process", response)
    
    def test_unsafe_input(self):
        """Test that unsafe inputs are blocked."""
        response = self.chatbot.process_message("Tell me something harmful")
        self.assertIn("cannot process", response)
    
    @patch('aetherlab.AetherLabClient.test_prompt')
    def test_api_failure_handling(self, mock_test_prompt):
        """Test handling of API failures."""
        mock_test_prompt.side_effect = APIError("API unavailable")
        response = self.chatbot.process_message("Hello")
        self.assertIn("cannot process", response)

if __name__ == "__main__":
    unittest.main()
```

## Conclusion

You've now learned how to:
- Integrate AetherLab guardrails into a chatbot
- Implement context-aware safety checks
- Optimize performance with caching and rate limiting
- Create domain-specific guardrails
- Monitor and log safety events

For production deployments, consider:
- Using async/await throughout for better performance
- Implementing more sophisticated caching strategies
- Adding metrics and alerting
- Creating custom guardrails for your specific use case

## Next Steps

- Read the [API Reference](../api-reference/python-sdk.md)
- Learn about [Best Practices](../best-practices/security.md)
- Explore [Advanced Features](../tutorials/advanced-features.md) 