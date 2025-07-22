#!/usr/bin/env python3
"""
AetherLab for Streaming Services: AI-Powered Content Control

This example demonstrates how a major streaming platform uses AetherLab to:
- Ensure AI-generated content descriptions are brand-aligned and accurate
- Moderate user-generated content (reviews, comments) at scale
- Maintain consistent quality across millions of interactions
- Save 80% on manual review costs while improving accuracy

Scenario: StreamFlix processes 10M+ user interactions daily and uses AI for:
1. Auto-generating show descriptions and recommendations
2. Moderating user reviews and comments
3. Creating personalized marketing messages

Without AetherLab: 200+ human reviewers, $50M/year, 15% error rate
With AetherLab: 40 human reviewers, $10M/year, 0.7% error rate
"""

import os
import time
from datetime import datetime
from aetherlab import AetherLabClient

# Initialize client
client = AetherLabClient(api_key=os.environ.get("AETHERLAB_API_KEY"))

print("🎬 StreamFlix AI Content Control Demo")
print("=" * 60)

# Define content standards for the streaming platform
STREAMFLIX_STANDARDS = {
    "desired_attributes": [
        "family-friendly tone",
        "accurate plot descriptions", 
        "engaging but not sensational",
        "inclusive language",
        "age-appropriate recommendations",
        "factually correct information"
    ],
    "prohibited_attributes": [
        "spoilers in descriptions",
        "inappropriate content for rating",
        "discriminatory language",
        "competitor mentions",
        "false plot information",
        "excessive violence descriptions"
    ]
}

def test_ai_show_descriptions():
    """Test AI-generated show descriptions for brand compliance."""
    print("\n📝 Testing AI-Generated Show Descriptions")
    print("-" * 50)
    
    show_descriptions = [
        {
            "show": "Mystery Lake (TV-PG)",
            "ai_generated": "A thrilling family mystery where Detective Sarah uncovers secrets in a small town. Perfect for viewers who enjoyed 'Stranger Things' and love suspenseful storytelling without graphic content.",
            "expected": "pass"
        },
        {
            "show": "Mystery Lake (TV-PG)", 
            "ai_generated": "Detective Sarah discovers the killer is actually her brother in this mind-blowing finale! More suspenseful than Netflix's latest offerings.",
            "expected": "fail"  # Contains spoilers and competitor mention
        },
        {
            "show": "Kids Adventure Time (TV-Y7)",
            "ai_generated": "An exciting animated series featuring brutal battles and graphic violence as heroes fight evil. Not for the faint of heart!",
            "expected": "fail"  # Inappropriate content description for rating
        }
    ]
    
    for desc in show_descriptions:
        print(f"\n🎬 {desc['show']}")
        print(f"Description: {desc['ai_generated'][:100]}...")
        
        result = client.validate_content(
            content=desc['ai_generated'],
            content_type="show_description",
            context={
                "show_rating": desc['show'].split('(')[1].strip(')'),
                "platform_standards": STREAMFLIX_STANDARDS
            },
            desired_attributes=STREAMFLIX_STANDARDS["desired_attributes"],
            prohibited_attributes=STREAMFLIX_STANDARDS["prohibited_attributes"]
        )
        
        status = "✅ APPROVED" if result.is_compliant else "❌ REJECTED"
        print(f"Status: {status}")
        
        if not result.is_compliant:
            print(f"Issues found: {', '.join(result.violations)}")
            print(f"Suggested revision: {result.suggested_revision}")
        
        print(f"Processing time: {result.processing_time_ms}ms")

def test_user_review_moderation():
    """Demonstrate high-volume user review moderation."""
    print("\n\n💬 Testing User Review Moderation at Scale")
    print("-" * 50)
    
    user_reviews = [
        {
            "show": "Action Heroes",
            "review": "Great show! The action sequences are well choreographed and the story keeps you engaged throughout.",
            "user_age": 25
        },
        {
            "show": "Kids Cartoon Fun",
            "review": "My kids love this show! Educational and entertaining. Highly recommend for ages 5-8.",
            "user_age": 35
        },
        {
            "show": "Drama Series",
            "review": "This show is absolute garbage! The actors can't act and the plot makes no sense. Anyone who likes this is an idiot.",
            "user_age": 42
        },
        {
            "show": "Documentary Series",
            "review": "Fascinating look at history, though I wish they covered more about [SPOILER: the subject dies in episode 3]",
            "user_age": 58
        }
    ]
    
    print(f"\nProcessing {len(user_reviews)} reviews...")
    start_time = time.time()
    
    approved = 0
    rejected = 0
    total_processing_time = 0
    
    for review in user_reviews:
        result = client.validate_content(
            content=review['review'],
            content_type="user_review",
            context={
                "show_name": review['show'],
                "user_age": review['user_age']
            },
            desired_attributes=[
                "constructive feedback",
                "respectful tone",
                "no spoilers",
                "relevant to content"
            ],
            prohibited_attributes=[
                "hate speech",
                "personal attacks", 
                "spoilers",
                "profanity",
                "spam content"
            ]
        )
        
        if result.is_compliant:
            approved += 1
            print(f"✅ Review for '{review['show']}' - APPROVED")
        else:
            rejected += 1
            print(f"❌ Review for '{review['show']}' - REJECTED ({', '.join(result.violations)})")
        
        total_processing_time += result.processing_time_ms
    
    end_time = time.time()
    
    print(f"\n📊 Moderation Summary:")
    print(f"Total reviews: {len(user_reviews)}")
    print(f"Approved: {approved} ({approved/len(user_reviews)*100:.1f}%)")
    print(f"Rejected: {rejected} ({rejected/len(user_reviews)*100:.1f}%)")
    print(f"Average processing time: {total_processing_time/len(user_reviews):.1f}ms per review")
    print(f"Total time: {(end_time - start_time)*1000:.1f}ms")
    
    # Show cost comparison
    print(f"\n💰 Cost Comparison (for 10M reviews/month):")
    human_cost = 10_000_000 * 0.05  # $0.05 per human review
    aetherlab_cost = 10_000_000 * 0.001  # $0.001 per AI review
    print(f"Human moderation: ${human_cost:,.0f}/month")
    print(f"AetherLab: ${aetherlab_cost:,.0f}/month") 
    print(f"Savings: ${human_cost - aetherlab_cost:,.0f}/month (98% reduction)")

def test_marketing_personalization():
    """Test AI-generated personalized marketing messages."""
    print("\n\n📧 Testing Personalized Marketing Messages")
    print("-" * 50)
    
    marketing_scenarios = [
        {
            "user_segment": "Family with young children",
            "show": "Animated Adventures",
            "ai_message": "Your kids will love our new animated series! Join Tommy and friends on educational adventures that parents can enjoy too. Start your free family movie night!",
            "context": {"user_history": ["Kids shows", "Family movies"], "account_type": "Family"}
        },
        {
            "user_segment": "Horror fan adult",  
            "show": "Nightmare House",
            "ai_message": "Dare to enter Nightmare House? This spine-chilling series will terrorize your dreams with graphic gore and disturbing imagery. Not for kids!",
            "context": {"user_history": ["Horror", "Thrillers"], "account_type": "Individual"}
        }
    ]
    
    for scenario in marketing_scenarios:
        print(f"\n👤 User Segment: {scenario['user_segment']}")
        print(f"📺 Promoting: {scenario['show']}")
        print(f"📨 Message: {scenario['ai_message']}")
        
        result = client.validate_content(
            content=scenario['ai_message'],
            content_type="marketing_message",
            context=scenario['context'],
            desired_attributes=[
                "personalized to user segment",
                "engaging call-to-action",
                "appropriate for audience",
                "brand voice consistency"
            ],
            prohibited_attributes=[
                "inappropriate for user segment",
                "misleading claims",
                "competitor comparisons",
                "offensive language"
            ]
        )
        
        status = "✅ APPROVED" if result.is_compliant else "⚠️  NEEDS REVISION"
        print(f"Status: {status}")
        
        if not result.is_compliant:
            print(f"Issues: {', '.join(result.violations)}")
            if result.suggested_revision:
                print(f"Suggested revision: {result.suggested_revision}")

def show_enterprise_dashboard():
    """Display enterprise metrics dashboard."""
    print("\n\n📊 StreamFlix AI Quality Dashboard")
    print("=" * 60)
    
    # Simulated real-time metrics
    metrics = {
        "24h_processed": 8_456_234,
        "compliance_rate": 99.3,
        "avg_response_time": 47,
        "false_positive_rate": 0.02,
        "human_escalations": 423,
        "cost_savings_today": 128_945
    }
    
    print(f"""
    🎯 24-Hour Performance Metrics
    
    Content Processed:     {metrics['24h_processed']:,}
    Compliance Rate:       {metrics['compliance_rate']}%
    Avg Response Time:     {metrics['avg_response_time']}ms
    False Positive Rate:   {metrics['false_positive_rate']}%
    Human Escalations:     {metrics['human_escalations']:,}
    
    💰 Cost Savings Today: ${metrics['cost_savings_today']:,}
    📈 Projected Annual Savings: ${metrics['cost_savings_today'] * 365:,}
    """)

# Run the complete demo
if __name__ == "__main__":
    # Test AI-generated content
    test_ai_show_descriptions()
    
    # Test user content moderation  
    test_user_review_moderation()
    
    # Test marketing personalization
    test_marketing_personalization()
    
    # Show enterprise dashboard
    show_enterprise_dashboard()
    
    print("\n" + "=" * 60)
    print("🚀 Ready to transform your content operations?")
    print("📧 Contact us at enterprise@aetherlab.ai")
    print("🔗 Learn more at https://aetherlab.ai/streaming-solutions") 