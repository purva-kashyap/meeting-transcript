"""
Zoom API Service
Handles all Zoom API interactions
"""

import os
import requests


class ZoomService:
    """Facade for Zoom API operations"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.base_url = os.getenv('ZOOM_BASE_URL', 'https://api.zoom.us')
        self.client_id = os.getenv('ZOOM_CLIENT_ID', '')
        self.client_secret = os.getenv('ZOOM_CLIENT_SECRET', '')
        
        # Mock data
        self.mock_users = {
            "user@example.com": "zoom_user_123",
            "test@test.com": "zoom_user_456"
        }
        
        self.mock_recordings = {
            "zoom_user_123": [
                {
                    "meeting_id": "zoom_meeting_001",
                    "topic": "Product Planning Session",
                    "start_time": "2025-12-28T10:00:00Z",
                    "duration": 45,
                    "recording_count": 1
                },
                {
                    "meeting_id": "zoom_meeting_002",
                    "topic": "Sprint Retrospective",
                    "start_time": "2025-12-27T14:30:00Z",
                    "duration": 60,
                    "recording_count": 1
                }
            ],
            "zoom_user_456": [
                {
                    "meeting_id": "zoom_meeting_003",
                    "topic": "Client Demo",
                    "start_time": "2025-12-26T11:00:00Z",
                    "duration": 30,
                    "recording_count": 1
                }
            ]
        }
        
        self.mock_transcripts = {
            "zoom_meeting_001": """Speaker 1 (00:00): Good morning everyone, thank you for joining today's product planning session.
Speaker 2 (00:15): Thanks for having us. Let's start with the Q1 roadmap.
Speaker 1 (00:30): Absolutely. We need to prioritize the new dashboard feature and mobile app improvements.
Speaker 2 (01:00): I agree. The analytics dashboard is critical for our enterprise customers.
Speaker 1 (01:30): Let's allocate two sprints for the dashboard and one for mobile optimization.
Speaker 2 (02:00): Sounds good. We should also consider the API enhancements.
Speaker 1 (02:30): Yes, API v2 should be in the Q1 scope. Let's schedule a technical review next week.""",
            "zoom_meeting_002": """Speaker 1 (00:00): Welcome to our sprint retrospective. Let's discuss what went well.
Speaker 2 (00:10): The deployment process was much smoother this sprint.
Speaker 3 (00:25): Agreed. The automated testing really helped catch bugs early.
Speaker 1 (00:45): Great points. What could we improve?
Speaker 2 (01:00): Communication during code reviews could be better.
Speaker 3 (01:15): Yes, and we should document our APIs more thoroughly.
Speaker 1 (01:40): Excellent feedback. Let's create action items for these improvements.""",
            "zoom_meeting_003": """Speaker 1 (00:00): Hello and welcome to the demo.
Speaker 2 (00:10): Thank you. We're excited to see the new features.
Speaker 1 (00:20): Let me share my screen and walk you through the updates.
Speaker 2 (00:40): This looks great! The new interface is very intuitive.
Speaker 1 (01:00): I'm glad you like it. Let me show you the reporting capabilities."""
        }
    
    def _get_access_token(self):
        """
        Get access token for Zoom API
        Implement OAuth flow as needed
        """
        if self.use_mock:
            return "mock_zoom_access_token"
        
        # TODO: Implement real Zoom OAuth flow
        # This would typically use OAuth 2.0 authorization code flow
        # or account-level app credentials
        raise NotImplementedError("Real Zoom authentication not yet implemented")
    
    def _make_api_call(self, endpoint, method="GET", data=None):
        """
        Make an authenticated call to Zoom API
        
        Args:
            endpoint: API endpoint (e.g., '/v2/users/email@example.com')
            method: HTTP method (GET, POST, etc.)
            data: Request body for POST requests
        
        Returns:
            Response JSON
        """
        if self.use_mock:
            return {"mock": True, "message": "Using mock data"}
        
        access_token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def get_user_id(self, email):
        """
        Get Zoom user ID from email
        
        Args:
            email: User email address
        
        Returns:
            User ID string
        """
        if self.use_mock:
            return self.mock_users.get(email, "zoom_user_default")
        
        # Real implementation: Call Zoom API
        try:
            endpoint = f"/v2/users/{email}"
            response = self._make_api_call(endpoint)
            return response.get('id')
        except Exception as e:
            raise Exception(f'Failed to fetch Zoom user: {str(e)}')
    
    def list_recordings(self, email):
        """
        Get list of recorded meetings for a user
        
        Args:
            email: User email address
        
        Returns:
            List of recording dictionaries
        """
        if self.use_mock:
            user_id = self.mock_users.get(email, "zoom_user_default")
            return self.mock_recordings.get(user_id, [])
        
        # Real implementation: Call Zoom API
        try:
            # First get user ID
            user_id = self.get_user_id(email)
            
            # Then get recordings
            endpoint = f"/v2/users/{user_id}/recordings"
            response = self._make_api_call(endpoint)
            
            recordings = []
            for meeting in response.get('meetings', []):
                recordings.append({
                    'meeting_id': meeting.get('uuid'),
                    'topic': meeting.get('topic'),
                    'start_time': meeting.get('start_time'),
                    'duration': meeting.get('duration'),
                    'recording_count': len(meeting.get('recording_files', []))
                })
            
            return recordings
        except Exception as e:
            raise Exception(f'Failed to fetch Zoom recordings: {str(e)}')
    
    def get_meeting_transcript(self, meeting_id):
        """
        Get transcript for a Zoom meeting
        
        Args:
            meeting_id: Meeting ID
        
        Returns:
            Transcript string
        """
        if self.use_mock:
            return self.mock_transcripts.get(meeting_id, "No transcript available for this meeting.")
        
        # Real implementation: Call Zoom API
        try:
            endpoint = f"/v2/meetings/{meeting_id}/recordings"
            response = self._make_api_call(endpoint)
            
            # Find transcript file in recordings
            recording_files = response.get('recording_files', [])
            for file in recording_files:
                if file.get('recording_type') == 'transcript':
                    # Download and return transcript content
                    transcript_url = file.get('download_url')
                    # TODO: Download and parse transcript file
                    return "Transcript content from Zoom API"
            
            return "No transcript available for this meeting."
        except Exception as e:
            raise Exception(f'Failed to fetch Zoom transcript: {str(e)}')
