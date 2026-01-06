from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

from services.zoom_service import ZoomService
from services.graph_service import GraphService
from services.llm_service import LLMService

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'

# Initialize services
zoom_service = ZoomService(use_mock=USE_MOCK_DATA)
graph_service = GraphService(use_mock=USE_MOCK_DATA)
llm_service = LLMService(use_mock=USE_MOCK_DATA)


# Routes
@app.route('/')
def home():
    """Home page with email input and meeting type buttons"""
    return render_template('home.html')


@app.route('/list/zoom/meetings', methods=['POST'])
def list_zoom_meetings():
    """Get list of Zoom meetings for a user and render meetings template"""
    try:
        # Handle both form data and JSON
        if request.is_json:
            email = request.get_json().get('email')
        else:
            email = request.form.get('email')
            
        if not email:
            # Render home with an error message if email missing
            return render_template('home.html', error='Email is required'), 400

        # Use Zoom service to get recordings
        recordings = zoom_service.list_recordings(email)

        # Render meetings template with server-side data
        return render_template('meetings.html', meetings=recordings, email=email, meetingType='zoom')

    except Exception as e:
        return render_template('home.html', error=str(e)), 500


@app.route('/zoom/meeting/<meeting_id>/summary', methods=['GET'])
def get_zoom_meeting_summary(meeting_id):
    """Get transcript and summary for a Zoom meeting and render summary template"""
    try:
        # Get transcript from Zoom service
        transcript = zoom_service.get_meeting_transcript(meeting_id)

        # Generate summary using LLM service
        summary = llm_service.generate_summary(transcript)

        # Mock participants for Zoom meetings (in real scenario, fetch from Zoom API)
        participants = [
            {"email": "participant1@example.com", "name": "Alice Johnson"},
            {"email": "participant2@example.com", "name": "Bob Smith"},
            {"email": "participant3@example.com", "name": "Carol Williams"}
        ]

        return render_template('summary.html', meeting_id=meeting_id, transcript=transcript, summary=summary, participants=participants, meetingType='zoom')

    except Exception as e:
        return render_template('meetings.html', error=str(e)), 500


@app.route('/list/teams/meetings', methods=['POST'])
def list_teams_meetings():
    """Get list of Teams meetings for a user and render meetings template"""
    try:
        # Handle both form data and JSON
        if request.is_json:
            email = request.get_json().get('email')
        else:
            email = request.form.get('email')
            
        if not email:
            return render_template('home.html', error='Email is required'), 400

        # Use Graph service to get meetings
        meetings = graph_service.list_meetings(email)

        return render_template('meetings.html', meetings=meetings, email=email, meetingType='teams')

    except Exception as e:
        return render_template('home.html', error=str(e)), 500


@app.route('/teams/meeting/<meeting_id>/summary', methods=['GET'])
def get_teams_meeting_summary(meeting_id):
    """Get transcript and summary for a Teams meeting and render summary template"""
    try:
        # Get transcript and participants from Graph service
        transcript, participants = graph_service.get_meeting_transcript(meeting_id)

        # Generate summary using LLM service
        summary = llm_service.generate_summary(transcript)

        return render_template('summary.html', meeting_id=meeting_id, transcript=transcript, summary=summary, participants=participants, meetingType='teams')

    except Exception as e:
        return render_template('meetings.html', error=str(e)), 500


@app.route('/teams/send-summary', methods=['POST'])
def send_summary_to_teams():
    """Create Teams chat and send summary to participants"""
    try:
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
            meeting_id = data.get('meeting_id')
            summary = data.get('summary')
            participants = data.get('participants', [])
        else:
            meeting_id = request.form.get('meeting_id')
            summary = request.form.get('summary')
            participants_str = request.form.get('participants', '[]')
            
            # Parse participants from JSON string if it's a string
            import json
            try:
                # Clean up the string and parse
                participants_str = participants_str.strip()
                if not participants_str or participants_str == '':
                    participants = []
                else:
                    participants = json.loads(participants_str)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing participants: {e}, value: {participants_str}")
                participants = []
            
        if not meeting_id or not summary:
            return render_template('summary.html', error='Meeting ID and summary are required'), 400

        # Use Graph service to send chat message
        result = graph_service.send_chat_message(meeting_id, summary, participants)

        # If result is a dict containing success, show meetings or summary page accordingly
        if isinstance(result, dict) and result.get('success'):
            # After sending, re-render summary with a success message
            return render_template('summary.html', meeting_id=meeting_id, transcript=None, summary=summary, participants=participants, message=result.get('message', 'Summary sent'), meetingType='teams')
        else:
            return render_template('summary.html', error=str(result)), 500

    except Exception as e:
        import traceback
        print(f"Error in send_summary_to_teams: {e}")
        print(traceback.format_exc())
        return render_template('summary.html', error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
