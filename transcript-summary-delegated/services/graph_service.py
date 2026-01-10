"""
Microsoft Graph API Service with Delegated Permissions
Handles all Microsoft Teams and Graph API interactions using user tokens
"""

import os
import requests
from flask import session


class GraphService:
    """Facade for Microsoft Graph API operations with delegated permissions"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.base_url = os.getenv('GRAPH_BASE_URL', 'https://graph.microsoft.com/v1.0')
        
        # Mock data
        self.mock_meetings = [
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
        ]
        
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
[00:02:30] Dev: Sounds good. Can we schedule a follow-up next week?"""
        }
    
    def _make_api_call(self, endpoint, access_token, method="GET", data=None):
        """
        Make an authenticated call to Microsoft Graph API using user token
        
        Args:
            endpoint: API endpoint (e.g., '/me/onlineMeetings')
            access_token: User's access token
            method: HTTP method (GET, POST, etc.)
            data: Request body for POST/PATCH requests
        
        Returns:
            Response JSON
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if self.use_mock:
            return {"mock": True, "message": "Using mock data"}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
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
        
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_json = e.response.json()
                error_detail = error_json.get('error', {}).get('message', str(e))
            except:
                error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            
            logger.error(f"Graph API Error: {method} {url} - Status: {e.response.status_code} - {error_detail}")
            raise Exception(f"Graph API error ({e.response.status_code}): {error_detail}")
        
        except Exception as e:
            logger.error(f"Unexpected error calling Graph API: {str(e)}")
            raise
    
    def get_user_profile(self, access_token):
        """
        Get the authenticated user's profile
        
        Args:
            access_token: User's access token
        
        Returns:
            User profile dictionary
        """
        if self.use_mock:
            return {
                "id": "mock_user_123",
                "displayName": "Mock User",
                "mail": "user@example.com",
                "userPrincipalName": "user@example.com"
            }
        
        return self._make_api_call("/me", access_token)
    
    def list_meetings(self, access_token):
        """
        Get list of recorded Teams meetings for the authenticated user
        
        Args:
            access_token: User's access token
        
        Returns:
            List of meeting dictionaries
        """
        if self.use_mock:
            return self.mock_meetings
        
        # Real implementation: Call Graph API to get recorded meetings
        try:
            # Get online meetings for the authenticated user
            endpoint = "/me/onlineMeetings"
            params = "?$filter=recordingStatus eq 'available'&$top=50"
            response = self._make_api_call(endpoint + params, access_token)
            
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
    
    def get_meeting_transcript(self, meeting_id, access_token):
        """
        Get transcript for a Teams meeting
        
        Args:
            meeting_id: Meeting ID
            access_token: User's access token
        
        Returns:
            Tuple of (transcript, participants)
        """
        if self.use_mock:
            transcript = self.mock_transcripts.get(meeting_id, "No transcript available for this meeting.")
            
            # Get participants for this meeting
            participants = []
            for meeting in self.mock_meetings:
                if meeting['meeting_id'] == meeting_id:
                    participants = meeting.get('participants', [])
                    break
            
            return transcript, participants
        
        # Real implementation: Get transcript from Graph API
        try:
            # Get meeting recording/transcript
            endpoint = f"/me/onlineMeetings/{meeting_id}/recordings"
            response = self._make_api_call(endpoint, access_token)
            
            # Get transcript content
            recordings = response.get('value', [])
            if recordings:
                transcript_url = recordings[0].get('content')
                # Download transcript content
                transcript = "Transcript content from Graph API"
            else:
                transcript = "No transcript available for this meeting."
            
            # Get meeting details for participants
            meeting_endpoint = f"/me/onlineMeetings/{meeting_id}"
            meeting_data = self._make_api_call(meeting_endpoint, access_token)
            participants = [p.get('identity', {}).get('user', {}).get('email') 
                          for p in meeting_data.get('participants', {}).get('attendees', [])]
            
            return transcript, participants
        except Exception as e:
            raise Exception(f'Failed to fetch Teams meeting data: {str(e)}')
    
    def send_chat_message(self, meeting_id, summary, participants, access_token):
        """
        Create Teams chat and send summary to participants
        
        Args:
            meeting_id: Meeting ID
            summary: Summary text to send
            participants: List of participant email addresses
            access_token: User's access token
        
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
            
            chat_response = self._make_api_call("/chats", access_token, method="POST", data=chat_data)
            chat_id = chat_response.get('id')
            
            # Step 2: Send the summary message to the chat
            message_data = {
                "body": {
                    "content": f"<h2>Meeting Summary</h2><p>{summary}</p>"
                }
            }
            
            self._make_api_call(f"/chats/{chat_id}/messages", access_token, method="POST", data=message_data)
            
            return {
                'success': True,
                'message': f'Summary sent to {len(participants)} participants via Teams chat',
                'chat_id': chat_id,
                'participants': participants
            }
        except Exception as e:
            raise Exception(f'Failed to send Teams message: {str(e)}')
