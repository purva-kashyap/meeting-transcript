from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
from dotenv import load_dotenv
from flask_session import Session
import msal

from services.auth_service import AuthService
from services.zoom_service import ZoomService
from services.graph_service import GraphService
from services.llm_service import LLMService

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure server-side session
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
app.config['SESSION_PERMANENT'] = os.getenv('SESSION_PERMANENT', 'false').lower() == 'true'
Session(app)

# Configuration
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'

# Initialize services
auth_service = AuthService(use_mock=USE_MOCK_DATA)
zoom_service = ZoomService(use_mock=USE_MOCK_DATA)
graph_service = GraphService(use_mock=USE_MOCK_DATA)
llm_service = LLMService(use_mock=USE_MOCK_DATA)


# Token cache helper functions
def _load_cache():
    """Load token cache from session"""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    """Save token cache to session"""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _get_token_from_cache():
    """Get valid access token from cache or refresh if needed"""
    cache = _load_cache()
    accounts = auth_service.get_accounts(cache=cache)
    
    if accounts:
        # Try to acquire token silently
        result = auth_service.acquire_token_silent(
            account=accounts[0],
            cache=cache
        )
        
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]
    
    return None


def _is_authenticated():
    """Check if user is authenticated"""
    if USE_MOCK_DATA:
        # In mock mode, consider user authenticated if they've visited the mock login
        return session.get("authenticated", False)
    
    return _get_token_from_cache() is not None


# Authentication routes
@app.route('/auth/login')
def auth_login():
    """Initiate Microsoft login flow"""
    # Generate state for CSRF protection
    state = str(uuid.uuid4())
    session["state"] = state
    session["email"] = request.args.get('email', '')  # Store email if provided
    
    # Check if we need to return to a specific page after login
    return_type = request.args.get('return_type')
    return_id = request.args.get('return_id')
    if return_type and return_id:
        session['returnToSummary'] = {
            'type': return_type,
            'id': return_id
        }
    
    # Get authorization URL
    auth_url = auth_service.get_login_url(state=state)
    
    return redirect(auth_url)


@app.route('/auth/mock-login')
def auth_mock_login():
    """Mock Microsoft login page for testing"""
    if not USE_MOCK_DATA:
        return redirect(url_for('auth_login'))
    
    return render_template('mock_login.html')


@app.route('/auth/mock-callback', methods=['POST'])
def auth_mock_callback():
    """Handle mock login submission"""
    if not USE_MOCK_DATA:
        return jsonify({'error': 'Mock authentication not available'}), 400
    
    # Simulate successful login
    session["authenticated"] = True
    session["user"] = {
        "name": "Mock User",
        "email": "user@example.com"
    }
    
    # Mock token acquisition
    cache = _load_cache()
    result = auth_service.acquire_token_by_auth_code(
        auth_code="mock_code",
        cache=cache
    )
    
    if result and "access_token" in result:
        session["access_token"] = result["access_token"]
        _save_cache(cache)
    
    # Check if user should return to summary page
    redirect_url = url_for('home')
    if session.get('returnToSummary'):
        summary_data = session.pop('returnToSummary')
        redirect_url = f"/summary.html?type={summary_data['type']}&id={summary_data['id']}"
    
    return jsonify({'success': True, 'redirect': redirect_url})


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Microsoft"""
    if USE_MOCK_DATA:
        return redirect(url_for('auth_mock_login'))
    
    # Verify state to prevent CSRF
    if request.args.get('state') != session.get("state"):
        return "State mismatch error", 400
    
    if "error" in request.args:
        return f"Authentication error: {request.args.get('error_description', request.args.get('error'))}", 400
    
    if "code" not in request.args:
        return "No authorization code received", 400
    
    # Exchange authorization code for token
    try:
        cache = _load_cache()
        result = auth_service.acquire_token_by_auth_code(
            auth_code=request.args['code'],
            cache=cache
        )
        
        if "access_token" in result:
            _save_cache(cache)
            
            # Get user profile
            user_profile = graph_service.get_user_profile(result["access_token"])
            session["user"] = {
                "name": user_profile.get("displayName"),
                "email": user_profile.get("mail") or user_profile.get("userPrincipalName")
            }
            
            # Check if user should return to summary page
            if session.get('returnToSummary'):
                summary_data = session.pop('returnToSummary')
                return redirect(f"/summary.html?type={summary_data['type']}&id={summary_data['id']}")
            
            return redirect(url_for('home'))
        else:
            return f"Failed to acquire token: {result.get('error_description', 'Unknown error')}", 400
    
    except Exception as e:
        return f"Authentication failed: {str(e)}", 500


@app.route('/auth/logout')
def auth_logout():
    """Logout user and clear session"""
    cache = _load_cache()
    accounts = auth_service.get_accounts(cache=cache)
    
    if accounts:
        auth_service.remove_account(accounts[0], cache=cache)
    
    session.clear()
    return redirect(url_for('home'))


@app.route('/auth/status')
def auth_status():
    """Check authentication status"""
    if _is_authenticated():
        return jsonify({
            'authenticated': True,
            'user': session.get('user', {})
        })
    else:
        return jsonify({
            'authenticated': False
        })


# Main application routes
@app.route('/')
def home():
    """Home page with email input and meeting type buttons"""
    return render_template('home.html', 
                         authenticated=_is_authenticated(),
                         user=session.get('user'))


@app.route('/meetings.html')
def meetings():
    """Meetings list page"""
    # No auth required for Zoom, but Teams will be checked in the API routes
    return render_template('meetings.html', user=session.get('user'))


@app.route('/summary.html')
def summary():
    """Summary page"""
    # No auth required for Zoom, but Teams will be checked in the API routes
    return render_template('summary.html', 
                         authenticated=_is_authenticated(),
                         user=session.get('user'))


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
    """Get list of Teams meetings for authenticated user"""
    try:
        if not _is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get access token
        access_token = _get_token_from_cache()
        if not access_token and USE_MOCK_DATA:
            access_token = session.get('access_token', 'mock_token')
        
        if not access_token:
            return jsonify({'error': 'No valid access token'}), 401
        
        # Use Graph service to get meetings
        meetings = graph_service.list_meetings(access_token)
        
        user_email = session.get('user', {}).get('email', 'user@example.com')
        
        return jsonify({
            'success': True,
            'meetings': meetings,
            'email': user_email
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/teams/meeting/<meeting_id>/summary', methods=['GET'])
def get_teams_meeting_summary(meeting_id):
    """Get transcript and summary for a Teams meeting"""
    try:
        if not _is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get access token
        access_token = _get_token_from_cache()
        if not access_token and USE_MOCK_DATA:
            access_token = session.get('access_token', 'mock_token')
        
        if not access_token:
            return jsonify({'error': 'No valid access token'}), 401
        
        # Get transcript and participants from Graph service
        transcript, participants = graph_service.get_meeting_transcript(meeting_id, access_token)
        
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
        if not _is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        meeting_id = data.get('meeting_id')
        summary = data.get('summary')
        participants = data.get('participants', [])
        
        if not meeting_id or not summary:
            return jsonify({'error': 'Meeting ID and summary are required'}), 400
        
        # Get access token
        access_token = _get_token_from_cache()
        if not access_token and USE_MOCK_DATA:
            access_token = session.get('access_token', 'mock_token')
        
        if not access_token:
            return jsonify({'error': 'No valid access token'}), 401
        
        # Use Graph service to send chat message
        result = graph_service.send_chat_message(meeting_id, summary, participants, access_token)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
