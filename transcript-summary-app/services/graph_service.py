"""
Microsoft Graph API Service
Handles all Microsoft Teams and Graph API interactions
"""

import os
import requests
from msal import ConfidentialClientApplication


class GraphService:
    """Facade for Microsoft Graph API operations"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.base_url = os.getenv('GRAPH_BASE_URL', 'https://graph.microsoft.com/v1.0')
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID', '')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET', '')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', '')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        # Mock data
        self.mock_meetings = {
            "user@example.com": [
                {
                    "meeting_id": "teams_meeting_001",
                    "subject": "Weekly Team Sync",
                    "start_time": "2025-12-29T09:00:00Z",
                    "end_time": "2025-12-29T09:30:00Z",
                    "participants": ["user@example.com", "colleague1@example.com", "colleague2@example.com"]
                },
                {
                    "meeting_id": "teams_meeting_002",
                    "subject": "Architecture Review",
                    "start_time": "2025-12-28T15:00:00Z",
                    "end_time": "2025-12-28T16:00:00Z",
                    "participants": ["user@example.com", "architect@example.com", "dev@example.com"]
                }
            ],
            "test@test.com": [
                {
                    "meeting_id": "teams_meeting_003",
                    "subject": "Customer Support Review",
                    "start_time": "2025-12-27T13:00:00Z",
                    "end_time": "2025-12-27T13:45:00Z",
                    "participants": ["test@test.com", "support@example.com"]
                }
            ]
        }
        
        self.mock_transcripts = {
            "teams_meeting_001": """[00:00:05] User: Good morning team, let's start with our weekly sync.
[00:00:15] Colleague 1: Morning! I've completed the user authentication module.
[00:00:30] Colleague 2: Great work! I'm still working on the payment integration.
[00:01:00] User: That's fine. What's your ETA on the payment module?
[00:01:15] Colleague 2: Should be done by end of week.
[00:01:30] User: Perfect. Let's also discuss the deployment strategy.
[00:02:00] Colleague 1: I suggest we do a staged rollout starting with beta users.""",
            "teams_meeting_002": """[00:00:05] User: Thanks for joining the architecture review.
[00:00:20] Architect: Happy to be here. Let's discuss the microservices design.
[00:00:40] Dev: I have some concerns about the service boundaries.
[00:01:00] Architect: That's a valid point. Let's review the domain model.
[00:01:30] User: We need to ensure scalability from day one.
[00:02:00] Architect: Agreed. I'll prepare a revised architecture document.
[00:02:30] Dev: Sounds good. Can we schedule a follow-up next week?""",
            "teams_meeting_003": """[00:00:05] Test User: Let's review this week's support tickets.
[00:00:15] Support: We had 45 tickets, most were resolved within 24 hours.
[00:00:35] Test User: Excellent response time. Any recurring issues?
[00:00:50] Support: Yes, several users reported login problems.
[00:01:10] Test User: Let's prioritize fixing the authentication flow.
[00:01:30] Support: I'll create a detailed bug report for the dev team."""
        }
    
    def _get_msal_app(self):
        """Initialize and return MSAL ConfidentialClientApplication"""
        if not self.client_id or not self.client_secret or not self.tenant_id:
            return None
        
        return ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def _get_access_token(self):
        """
        Get access token for Microsoft Graph API using client credentials flow
        (Application permissions)
        """
        if self.use_mock:
            return "mock_access_token"
        
        msal_app = self._get_msal_app()
        if not msal_app:
            raise Exception("Microsoft Graph credentials not configured")
        
        # Acquire token using client credentials (application permissions)
        result = msal_app.acquire_token_for_client(scopes=self.scopes)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            error_description = result.get("error_description", "Unknown error")
            raise Exception(f"Failed to acquire token: {error_description}")
    
    def _make_api_call(self, endpoint, method="GET", data=None):
        """
        Make an authenticated call to Microsoft Graph API
        
        Args:
            endpoint: API endpoint (e.g., '/users/user@example.com/onlineMeetings')
            method: HTTP method (GET, POST, etc.)
            data: Request body for POST/PATCH requests
        
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
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def list_meetings(self, email):
        """
        Get list of recorded Teams meetings for a user
        
        Args:
            email: User email address
        
        Returns:
            List of meeting dictionaries
        """
        if self.use_mock:
            return self.mock_meetings.get(email, [])
        
        # Real implementation: Call Graph API to get recorded meetings
        try:
            # Get online meetings for the user
            endpoint = f"/users/{email}/onlineMeetings"
            params = "?$filter=recordingStatus eq 'available'&$top=50"
            response = self._make_api_call(endpoint + params)
            
            meetings = []
            for meeting in response.get('value', []):
                meetings.append({
                    'meeting_id': meeting.get('id'),
                    'subject': meeting.get('subject', 'No subject'),
                    'start_time': meeting.get('startDateTime'),
                    'end_time': meeting.get('endDateTime'),
                    'participants': [p.get('identity', {}).get('user', {}).get('email') 
                                   for p in meeting.get('participants', {}).get('attendees', [])]
                })
            return meetings
        except Exception as e:
            raise Exception(f'Failed to fetch Teams meetings: {str(e)}')
    
    def get_meeting_transcript(self, meeting_id):
        """
        Get transcript for a Teams meeting
        
        Args:
            meeting_id: Meeting ID
        
        Returns:
            Tuple of (transcript, participants)
        """
        if self.use_mock:
            transcript = self.mock_transcripts.get(meeting_id, "No transcript available for this meeting.")
            
            # Get participants for this meeting
            participants = []
            for meetings in self.mock_meetings.values():
                for meeting in meetings:
                    if meeting['meeting_id'] == meeting_id:
                        participants = meeting.get('participants', [])
                        break
            
            return transcript, participants
        
        # Real implementation: Get transcript from Graph API
        try:
            # Get meeting recording/transcript
            endpoint = f"/users/me/onlineMeetings/{meeting_id}/recordings"
            response = self._make_api_call(endpoint)
            
            # Get transcript content
            # Note: The actual implementation depends on your Graph API setup
            # This is a simplified version
            recordings = response.get('value', [])
            if recordings:
                transcript_url = recordings[0].get('content')
                # Download transcript content
                transcript = "Transcript content from Graph API"
            else:
                transcript = "No transcript available for this meeting."
            
            # Get meeting details for participants
            meeting_endpoint = f"/users/me/onlineMeetings/{meeting_id}"
            meeting_data = self._make_api_call(meeting_endpoint)
            participants = [p.get('identity', {}).get('user', {}).get('email') 
                          for p in meeting_data.get('participants', {}).get('attendees', [])]
            
            return transcript, participants
        except Exception as e:
            raise Exception(f'Failed to fetch Teams meeting data: {str(e)}')
    
    def send_chat_message(self, meeting_id, summary, participants):
        """
        Create Teams chat and send summary to participants
        
        Args:
            meeting_id: Meeting ID
            summary: Summary text to send
            participants: List of participant email addresses
        
        Returns:
            Dictionary with success status and chat details
        """
        if self.use_mock:
            return {
                'success': True,
                'message': f'Summary sent to {len(participants)} participants via Teams chat',
                'chat_id': f'mock_chat_{meeting_id}',
                'participants': participants
            }
        
        # Real implementation: Create group chat and send message via Graph API
        try:
            # Step 1: Create a group chat with participants
            chat_members = []
            for participant_email in participants:
                chat_members.append({
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{participant_email}')"
                })
            
            chat_data = {
                "chatType": "group",
                "topic": f"Meeting Summary - {meeting_id}",
                "members": chat_members
            }
            
            chat_response = self._make_api_call("/chats", method="POST", data=chat_data)
            chat_id = chat_response.get('id')
            
            # Step 2: Send the summary message to the chat
            message_data = {
                "body": {
                    "content": f"<h2>Meeting Summary</h2><p>{summary}</p>"
                }
            }
            
            self._make_api_call(f"/chats/{chat_id}/messages", method="POST", data=message_data)
            
            return {
                'success': True,
                'message': f'Summary sent to {len(participants)} participants via Teams chat',
                'chat_id': chat_id,
                'participants': participants
            }
        except Exception as e:
            raise Exception(f'Failed to send Teams message: {str(e)}')
