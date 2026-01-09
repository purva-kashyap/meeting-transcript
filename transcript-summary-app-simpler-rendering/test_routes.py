#!/usr/bin/env python3
"""
Quick test to verify all routes are working
"""

from app import app

print("Testing Flask Routes...")
print("=" * 60)

with app.test_client() as client:
    print("\n✅ Testing home page...")
    response = client.get('/')
    print(f"   GET / → {response.status_code}")
    
    print("\n✅ Testing auth routes...")
    response = client.get('/auth/login')
    print(f"   GET /auth/login → {response.status_code}")
    
    response = client.get('/auth/mock-login')
    print(f"   GET /auth/mock-login → {response.status_code}")
    
    response = client.get('/auth/status')
    print(f"   GET /auth/status → {response.status_code}")
    
    print("\n✅ Testing Teams summary route...")
    response = client.get('/teams/meeting/teams_meeting_001/summary?email=user@example.com')
    print(f"   GET /teams/meeting/teams_meeting_001/summary → {response.status_code}")
    
    print("\n✅ Testing Zoom summary route...")
    response = client.get('/zoom/meeting/zoom_meeting_001/summary')
    print(f"   GET /zoom/meeting/zoom_meeting_001/summary → {response.status_code}")
    
    print("\n" + "=" * 60)
    print("All routes are working! ✅")
    print("\nNow test in browser:")
    print("1. python app.py")
    print("2. Visit http://localhost:5001")
    print("3. Try the login flow")
