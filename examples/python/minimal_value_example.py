from aetherlab import AetherLabClient

# Initialize AetherLab
client = AetherLabClient(api_key="your-api-key")

# AI generates a response that could be risky
ai_response = "You should definitely invest all your savings in crypto! Guaranteed 10x returns!"

# AetherLab analyzes the content
result = client.validate_content(
    content=ai_response,
    content_type="financial_advice",
    desired_attributes=["professional", "accurate", "includes disclaimers"],
    prohibited_attributes=["guaranteed returns", "financial advice without disclaimer"]
)

# Key metrics:
print(f"Compliant: {'✅ Yes' if result.is_compliant else '❌ No'}")
print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")
print(f"Confidence in compliance: {result.confidence_score:.1%}")

if not result.is_compliant:
    print(f"\nViolations: {result.violations}")
    print(f"\nSuggested revision: {result.suggested_revision}") 