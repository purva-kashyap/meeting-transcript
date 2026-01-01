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


@app.route('/meetings.html')
def meetings():
    """Meetings list page"""
    return render_template('meetings.html')


@app.route('/summary.html')
def summary():
    """Summary page"""
    return render_template('summary.html')


@app.route('/list/zoom/meetings', methods=['POST'])
def list_zoom_meetings():
    """Get list of Zoom meetings for a user"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Use Zoom service to get recordings
        recordings = zoom_service.list_recordings(email)
        
        return jsonify({
            'success': True,
            'meetings': recordings,
            'email': email
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/zoom/meeting/<meeting_id>/summary', methods=['GET'])
def get_zoom_meeting_summary(meeting_id):
    """Get transcript and summary for a Zoom meeting"""
    try:
        # Get transcript from Zoom service
        transcript = zoom_service.get_meeting_transcript(meeting_id)
        
        # Generate summary using LLM service
        summary = llm_service.generate_summary(transcript)
        
        return jsonify({
            'success': True,
            'meeting_id': meeting_id,
            'transcript': transcript,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list/teams/meetings', methods=['POST'])
def list_teams_meetings():
    """Get list of Teams meetings for a user"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Use Graph service to get meetings
        meetings = graph_service.list_meetings(email)
        
        return jsonify({
            'success': True,
            'meetings': meetings,
            'email': email
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/teams/meeting/<meeting_id>/summary', methods=['GET'])
def get_teams_meeting_summary(meeting_id):
    """Get transcript and summary for a Teams meeting"""
    try:
        # Get transcript and participants from Graph service
        transcript, participants = graph_service.get_meeting_transcript(meeting_id)
        
        # Generate summary using LLM service
        summary = llm_service.generate_summary(transcript)
        
        return jsonify({
            'success': True,
            'meeting_id': meeting_id,
            'transcript': transcript,
            'summary': summary,
            'participants': participants
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/teams/send-summary', methods=['POST'])
def send_summary_to_teams():
    """Create Teams chat and send summary to participants"""
    try:
        data = request.get_json()
        meeting_id = data.get('meeting_id')
        summary = data.get('summary')
        participants = data.get('participants', [])
        
        if not meeting_id or not summary:
            return jsonify({'error': 'Meeting ID and summary are required'}), 400
        
        # Use Graph service to send chat message
        result = graph_service.send_chat_message(meeting_id, summary, participants)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
