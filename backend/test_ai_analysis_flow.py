#!/usr/bin/env python3
"""
Test script to simulate the exact flow when clicking on an economic event
"""

import requests
import json
import time

def test_ai_analysis_flow():
    """Test the complete AI analysis flow"""
    
    print("🧪 Testing Complete AI Analysis Flow")
    print("=" * 50)
    
    # Step 1: Get economic calendar data
    print("📅 Step 1: Getting economic calendar data...")
    try:
        calendar_response = requests.get("http://localhost:5001/api/economic-calendar?start_date=2025-08-14&end_date=2025-08-14")
        if calendar_response.status_code == 200:
            calendar_data = calendar_response.json()
            events = calendar_data.get('events', [])
            print(f"✅ Found {len(events)} economic events")
            
            if events:
                # Get the first event
                event = events[0]
                print(f"📊 Testing with event: {event.get('title', 'Unknown')}")
                
                # Step 2: Call the enhanced analysis endpoint
                print("🤖 Step 2: Calling enhanced analysis endpoint...")
                
                # Prepare the request data (same as frontend)
                request_data = {
                    "event": event,
                    "analysisType": "pre-event",
                    "marketContext": {
                        "currentTime": "2024-08-14T15:30:00.000Z",
                        "eventTime": "2024-08-14T14:30:00.000Z",
                        "isPostEvent": False
                    }
                }
                
                # Make the request
                analysis_response = requests.post(
                    f"http://localhost:5001/api/enhanced-analysis/{event.get('id', 1)}",
                    headers={"Content-Type": "application/json"},
                    json=request_data
                )
                
                if analysis_response.status_code == 200:
                    analysis_data = analysis_response.json()
                    print("✅ Enhanced analysis response received!")
                    
                    # Check the content
                    print("\n📊 Content Analysis:")
                    general_overview = analysis_data.get('general_overview', {})
                    immediate_impact = analysis_data.get('immediate_impact', {})
                    
                    event_explanation = general_overview.get('event_explanation', '')
                    market_logic = general_overview.get('market_logic', '')
                    detailed_analysis = immediate_impact.get('detailed_analysis', '')
                    
                    print(f"   Event Explanation Length: {len(event_explanation)}")
                    print(f"   Market Logic Length: {len(market_logic)}")
                    print(f"   Detailed Analysis Length: {len(detailed_analysis)}")
                    
                    print(f"\n📖 Sample Content:")
                    print(f"   Event Explanation: {event_explanation[:100]}...")
                    print(f"   Market Logic: {market_logic[:100]}...")
                    print(f"   Detailed Analysis: {detailed_analysis[:100]}...")
                    
                    # Check if this is fallback content
                    model_used = analysis_data.get('model_used', 'unknown')
                    if model_used == "fallback":
                        print(f"\n⚠️ WARNING: Using fallback analysis!")
                        print(f"   This means the GPT API call failed.")
                    else:
                        print(f"\n✅ SUCCESS: Using real GPT analysis!")
                        print(f"   Model: {model_used}")
                        print(f"   Detailed paragraphs should be displayed.")
                    
                    return analysis_data
                    
                else:
                    print(f"❌ Enhanced analysis failed: {analysis_response.status_code}")
                    print(f"   Response: {analysis_response.text}")
                    return None
            else:
                print("❌ No economic events found")
                return None
        else:
            print(f"❌ Failed to get calendar data: {calendar_response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is the backend running?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting AI Analysis Flow Test...")
    result = test_ai_analysis_flow()
    
    if result:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n💥 Test failed!")
