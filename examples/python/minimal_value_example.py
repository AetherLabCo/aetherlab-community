from aetherlab import AetherLabClient

# Initialize AetherLab
client = AetherLabClient(api_key="your-api-key")

# AI generates a response that could be risky
ai_response = "You should definitely invest all your savings in crypto! Guaranteed 10x returns!"

# AetherLab ensures it's safe and compliant
result = client.validate_content(
    content=ai_response,
    content_type="financial_advice",
    desired_attributes=["professional", "accurate", "includes disclaimers"],
    prohibited_attributes=["guaranteed returns", "financial advice without disclaimer"]
)

if result.is_compliant:
    print(f"✅ Safe to send: {result.content}")
else:
    print(f"🚫 Blocked: {result.violations}")
    print(f"✅ Safe alternative: {result.suggested_revision}") 