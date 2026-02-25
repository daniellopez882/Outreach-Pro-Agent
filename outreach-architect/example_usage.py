"""
Example Usage - Personalized Outreach Architect

This script demonstrates how to use the system end-to-end
"""
import asyncio
import httpx
from typing import List, Dict


BASE_URL = "http://localhost:8000"


async def example_full_workflow():
    """
    Complete example workflow:
    1. Add leads
    2. Generate personalized campaigns
    3. Review results
    4. Send emails
    """
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        print("=" * 80)
        print("PERSONALIZED OUTREACH ARCHITECT - Example Workflow")
        print("=" * 80)
        
        # Step 1: Create leads
        print("\n📋 Step 1: Creating test leads...")
        
        leads = [
            {
                "name": "Rahul Sharma",
                "email": "rahul.sharma@techcorp.com",
                "company": "TechCorp India",
                "job_title": "VP of Engineering",
                "linkedin_url": "https://linkedin.com/in/rahulsharma",
                "location": "Mumbai, India",
                "company_website": "https://techcorp.in",
                "source": "linkedin_search"
            },
            {
                "name": "Priya Patel",
                "email": "priya@startup.io",
                "company": "InnovateTech",
                "job_title": "CTO",
                "linkedin_url": "https://linkedin.com/in/priyapatel",
                "location": "Bangalore, India",
                "company_website": "https://innovatetech.io",
                "source": "referral"
            }
        ]
        
        lead_ids = []
        
        for lead_data in leads:
            response = await client.post(f"{BASE_URL}/leads", json=lead_data)
            if response.status_code == 200:
                lead = response.json()
                lead_ids.append(lead['id'])
                print(f"  ✓ Created: {lead['name']} (ID: {lead['id']})")
            else:
                print(f"  ✗ Failed to create {lead_data['name']}: {response.text}")
        
        # Step 2: Generate personalized campaigns
        print("\n🤖 Step 2: Generating hyper-personalized emails with Kimi AI...")
        
        campaign_request = {
            "lead_ids": lead_ids,
            "company_context": """
                We are DevTools Pro, a developer productivity platform that helps 
                engineering teams ship code 3x faster through intelligent code reviews, 
                automated testing, and CI/CD optimization.
                
                Our clients include top tech companies in India and Southeast Asia.
                We've helped reduce deployment times by 60% and cut bug rates by 40%.
            """,
            "value_proposition": """
                I noticed your team is growing rapidly (15+ engineering openings on LinkedIn).
                With that growth comes deployment complexity and quality challenges.
                
                We've helped similar companies maintain velocity while scaling - 
                would love to share how companies like Razorpay and Zomato cut their 
                deployment times in half.
            """,
            "auto_send": False  # Review before sending
        }
        
        response = await client.post(f"{BASE_URL}/campaigns", json=campaign_request)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n  Status: {result['status']}")
            
            if result['status'] == 'completed':
                stats = result.get('statistics', {})
                print(f"\n  📊 Results:")
                print(f"     Total: {stats.get('total', 0)}")
                print(f"     Successful: {stats.get('successful', 0)}")
                print(f"     Low Relevance (skipped): {stats.get('low_relevance', 0)}")
                print(f"     Failed: {stats.get('failed', 0)}")
                
                # Show sample generated emails
                results = result.get('results', [])
                for idx, res in enumerate(results[:2], 1):  # Show first 2
                    print(f"\n  📧 Sample Email #{idx}:")
                    if 'stages' in res and 'email_generation' in res['stages']:
                        email = res['stages']['email_generation']
                        print(f"     Subject: {email.get('subject_line', 'N/A')}")
                        print(f"     Personalization: {len(email.get('personalization_elements', []))} elements")
                        print(f"     Quality Score: {res['stages']['quality_check'].get('quality_score', 0):.2f}")
        
        # Step 3: List campaigns
        print("\n📋 Step 3: Listing generated campaigns...")
        
        response = await client.get(f"{BASE_URL}/campaigns")
        if response.status_code == 200:
            campaigns = response.json()
            print(f"\n  Found {len(campaigns)} campaigns:")
            for camp in campaigns:
                print(f"\n  Campaign #{camp['id']}:")
                print(f"     Lead: {camp['lead_id']}")
                print(f"     Status: {camp['status']}")
                print(f"     Subject: {camp['subject_line'][:60]}...")
                print(f"     Personalization: {len(camp['personalization_elements'])} elements")
        
        # Step 4: Send a campaign (example)
        print("\n📤 Step 4: Sending a campaign (example - not actually sending)...")
        
        if campaigns:
            campaign_id = campaigns[0]['id']
            print(f"  Would send campaign #{campaign_id}")
            print("  To actually send: POST /campaigns/{campaign_id}/send")
            
            # Uncomment to actually send:
            # response = await client.post(f"{BASE_URL}/campaigns/{campaign_id}/send")
            # if response.status_code == 200:
            #     print("  ✓ Email sent!")
        
        # Step 5: Check analytics
        print("\n📊 Step 5: Analytics...")
        
        response = await client.get(f"{BASE_URL}/analytics/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n  Total Leads: {stats['total_leads']}")
            print(f"  Total Campaigns: {stats['total_campaigns']}")
            print(f"  Sent: {stats['sent_campaigns']}")
            print(f"  Replied: {stats['replied_campaigns']}")
            print(f"  Response Rate: {stats['response_rate']}% (Target: {stats['target_response_rate']})")
        
        print("\n" + "=" * 80)
        print("✅ Workflow complete!")
        print("=" * 80)


async def example_single_lead_processing():
    """
    Process a single high-value lead with maximum personalization
    """
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        print("\n🎯 Single High-Value Lead Processing\n")
        
        # Create lead
        lead_data = {
            "name": "Amit Kumar",
            "email": "amit.kumar@unicorn.com",
            "company": "Unicorn Startup",
            "job_title": "Head of Product",
            "linkedin_url": "https://linkedin.com/in/amitkumar",
            "company_website": "https://unicorn.com"
        }
        
        response = await client.post(f"{BASE_URL}/leads", json=lead_data)
        lead = response.json()
        
        print(f"Created lead: {lead['name']}")
        
        # Generate campaign with A/B variants
        campaign_request = {
            "lead_ids": [lead['id']],
            "company_context": "AI-powered sales enablement platform",
            "value_proposition": "Increase sales team productivity by 40%",
            "auto_send": False,
            "generate_ab_variants": True
        }
        
        response = await client.post(f"{BASE_URL}/campaigns", json=campaign_request)
        result = response.json()
        
        print(f"\nCampaign generated!")
        print(f"Status: {result['status']}")


async def example_bulk_import():
    """
    Bulk import leads from a list
    """
    
    # In production, this could come from:
    # - CSV file
    # - LinkedIn Sales Navigator export
    # - CRM integration
    # - Web scraping results
    
    leads_data = [
        {
            "name": f"Lead {i}",
            "email": f"lead{i}@company.com",
            "company": f"Company {i}",
            "job_title": "Software Engineer",
            "source": "bulk_import"
        }
        for i in range(1, 11)  # 10 leads
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        print(f"\n📥 Bulk importing {len(leads_data)} leads...\n")
        
        created_count = 0
        
        for lead_data in leads_data:
            try:
                response = await client.post(f"{BASE_URL}/leads", json=lead_data)
                if response.status_code == 200:
                    created_count += 1
                    print(f"  ✓ Created: {lead_data['name']}")
                else:
                    print(f"  ✗ Failed: {lead_data['name']}")
            except Exception as e:
                print(f"  ✗ Error: {lead_data['name']} - {e}")
        
        print(f"\n✅ Created {created_count}/{len(leads_data)} leads")


if __name__ == "__main__":
    print("""
    🚀 Personalized Outreach Architect - Examples
    
    Choose an example to run:
    1. Full workflow (recommended for first time)
    2. Single high-value lead
    3. Bulk import
    
    Make sure the API server is running:
    python main.py
    """)
    
    # Run the full workflow example
    asyncio.run(example_full_workflow())
    
    # Uncomment to run other examples:
    # asyncio.run(example_single_lead_processing())
    # asyncio.run(example_bulk_import())
