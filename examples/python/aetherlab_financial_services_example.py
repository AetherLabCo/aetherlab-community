#!/usr/bin/env python3
"""
AetherLab for Financial Services: Compliant AI Customer Experience

This example shows how a major bank uses AetherLab to ensure their AI systems:
- Never give incorrect financial advice or misleading information
- Maintain regulatory compliance (SEC, FINRA, GDPR)
- Protect customer privacy and sensitive data
- Provide consistent, professional service across all channels

Scenario: GlobalBank handles 5M+ customer interactions monthly via:
- AI chatbots for account inquiries
- Automated loan application reviews  
- Investment recommendation engines
- Fraud alert communications

Business Impact:
- 99.8% compliance rate (vs 94% with manual review)
- 75% reduction in compliance violations
- $30M annual savings in compliance costs
- 3x faster response times
"""

import os
from aetherlab import AetherLabClient
from datetime import datetime
import json

# Initialize client
client = AetherLabClient(api_key=os.environ.get("AETHERLAB_API_KEY"))

print("🏦 GlobalBank AI Compliance Demo")
print("=" * 60)

# Financial services compliance standards
COMPLIANCE_STANDARDS = {
    "desired_attributes": [
        "factually accurate information",
        "clear disclaimer when appropriate",
        "professional tone",
        "no financial advice without license",
        "data privacy protection",
        "audit trail capability"
    ],
    "prohibited_attributes": [
        "guaranteed returns claims",
        "unlicensed financial advice", 
        "sharing personal data",
        "misleading information",
        "high-pressure sales tactics",
        "discriminatory language"
    ]
}

def test_customer_service_chatbot():
    """Test AI chatbot responses for compliance and quality."""
    print("\n💬 Testing Customer Service Chatbot Responses")
    print("-" * 50)
    
    customer_queries = [
        {
            "query": "What's my account balance?",
            "ai_response": "I can help you check your account balance. For security, please verify your identity by logging into our secure portal or visiting a branch with valid ID.",
            "context": {"authenticated": False}
        },
        {
            "query": "Should I invest in crypto?",
            "ai_response": "Cryptocurrency investments carry significant risks and volatility. I recommend speaking with our licensed financial advisors who can assess your personal situation. Would you like to schedule a consultation?",
            "context": {"user_type": "retail_customer"}
        },
        {
            "query": "Should I invest in crypto?", 
            "ai_response": "You should definitely buy Bitcoin now! It's guaranteed to double in value by next month. Transfer your savings immediately!",
            "context": {"user_type": "retail_customer"}
        },
        {
            "query": "Why was I charged a fee?",
            "ai_response": "I see a $35 overdraft fee on your account from March 15. This occurs when your balance goes below $0. You can avoid this with our overdraft protection service. Would you like more information?",
            "context": {"authenticated": True, "account_data": "sanitized"}
        }
    ]
    
    for i, interaction in enumerate(customer_queries):
        print(f"\n🤔 Customer: {interaction['query']}")
        print(f"🤖 AI Response: {interaction['ai_response'][:100]}...")
        
        result = client.validate_content(
            content=interaction['ai_response'],
            content_type="financial_chatbot_response",
            context=interaction['context'],
            desired_attributes=COMPLIANCE_STANDARDS["desired_attributes"],
            prohibited_attributes=COMPLIANCE_STANDARDS["prohibited_attributes"],
            regulations=["SEC", "FINRA", "GDPR", "CCPA"]
        )
        
        status = "✅ COMPLIANT" if result.is_compliant else "🚫 NON-COMPLIANT"
        print(f"Status: {status}")
        
        if not result.is_compliant:
            print(f"Violations: {', '.join(result.violations)}")
            print(f"Regulatory risks: {', '.join(result.regulatory_risks)}")
            print(f"Suggested revision: {result.suggested_revision}")
        
        # Show audit trail capability
        print(f"Audit ID: {result.audit_id}")
        print(f"Timestamp: {result.timestamp}")

def test_loan_communications():
    """Test automated loan decision communications."""
    print("\n\n📋 Testing Automated Loan Communications")
    print("-" * 50)
    
    loan_scenarios = [
        {
            "scenario": "Loan Approval",
            "ai_message": "Congratulations! Your loan application #LN-2024-0892 has been approved for $50,000 at 6.99% APR. Terms: 60 months. Documents will arrive within 3 business days. This offer is valid for 30 days.",
            "context": {"loan_status": "approved", "customer_tier": "prime"}
        },
        {
            "scenario": "Loan Denial - Risky Version",
            "ai_message": "Your loan was denied because you're poor and have bad credit. Try again when you make more money.",
            "context": {"loan_status": "denied", "denial_reason": "credit_score"}
        },
        {
            "scenario": "Loan Denial - Compliant Version",
            "ai_message": "Thank you for your loan application. After careful review, we're unable to approve your request at this time. You'll receive a detailed adverse action notice within 7 days explaining this decision and your rights. Our credit counseling team can help explore alternatives: 1-800-XXX-XXXX.",
            "context": {"loan_status": "denied", "denial_reason": "credit_score"}
        }
    ]
    
    for scenario in loan_scenarios:
        print(f"\n📧 Scenario: {scenario['scenario']}")
        print(f"Message: {scenario['ai_message'][:100]}...")
        
        result = client.validate_content(
            content=scenario['ai_message'],
            content_type="loan_communication",
            context=scenario['context'],
            desired_attributes=[
                "clear communication",
                "regulatory compliance",
                "professional tone",
                "accurate information",
                "appropriate disclaimers"
            ],
            prohibited_attributes=[
                "discriminatory language",
                "misleading terms",
                "missing required disclosures",
                "inappropriate tone"
            ],
            regulations=["FCRA", "ECOA", "TILA"]
        )
        
        print(f"Compliance: {'✅ PASS' if result.is_compliant else '❌ FAIL'}")
        if not result.is_compliant:
            print(f"Issues: {result.compliance_report}")

def test_investment_recommendations():
    """Test AI-generated investment recommendations."""
    print("\n\n📈 Testing Investment Recommendation Engine")
    print("-" * 50)
    
    recommendations = [
        {
            "client_profile": "Conservative retiree",
            "ai_recommendation": "Based on your risk profile, consider a diversified portfolio of 70% bonds and 30% equities. Past performance doesn't guarantee future results. Consult with your financial advisor before making investment decisions.",
            "includes_required": ["disclaimer", "risk_appropriate"]
        },
        {
            "client_profile": "Young professional", 
            "ai_recommendation": "YOLO into meme stocks! 🚀 Drop your entire 401k into GME calls. Can't lose! Not financial advice tho 😉",
            "includes_required": []
        }
    ]
    
    for rec in recommendations:
        print(f"\n👤 Client Profile: {rec['client_profile']}")
        print(f"🤖 AI Recommendation: {rec['ai_recommendation']}")
        
        result = client.validate_content(
            content=rec['ai_recommendation'],
            content_type="investment_recommendation",
            context={
                "client_type": rec['client_profile'],
                "channel": "digital_platform"
            },
            desired_attributes=[
                "appropriate disclaimers",
                "risk-appropriate advice",
                "professional language",
                "educational tone"
            ],
            prohibited_attributes=[
                "guaranteed returns",
                "get rich quick schemes",
                "unlicensed advice",
                "meme stock promotion"
            ],
            regulations=["SEC", "FINRA Rule 2111"]
        )
        
        print(f"Status: {'✅ COMPLIANT' if result.is_compliant else '🚫 VIOLATION'}")
        print(f"Risk Score: {result.risk_score}/10")
        
def show_compliance_dashboard():
    """Show real-time compliance monitoring dashboard."""
    print("\n\n📊 GlobalBank AI Compliance Dashboard")
    print("=" * 60)
    
    print("""
    🔍 Last 24 Hours Overview
    
    Total AI Interactions:        156,892
    Compliance Rate:              99.82%
    Blocked Responses:            283
    Human Escalations:            47
    
    📋 Regulatory Breakdown:
    SEC Compliance:               99.94%
    FINRA Compliance:            99.89%
    GDPR Compliance:             99.97%
    FCRA Compliance:             99.91%
    
    ⚠️  Recent Alerts:
    - 3 potential unlicensed advice attempts blocked
    - 1 data privacy near-miss (prevented)
    - 5 high-pressure sales tactics filtered
    
    💰 Compliance Cost Savings:
    Manual Review Cost:           $78,446/day
    AetherLab Cost:              $15,689/day
    Daily Savings:               $62,757
    Annual Projection:           $22.9M saved
    """)

# Run the complete demo
if __name__ == "__main__":
    # Test chatbot compliance
    test_customer_service_chatbot()
    
    # Test loan communications
    test_loan_communications()
    
    # Test investment recommendations
    test_investment_recommendations()
    
    # Show compliance dashboard
    show_compliance_dashboard()
    
    print("\n" + "=" * 60)
    print("🛡️  Ensure 100% AI compliance with AetherLab")
    print("📞 Schedule a demo: sales@aetherlab.ai")
    print("📚 Compliance guide: aetherlab.ai/financial-compliance") 