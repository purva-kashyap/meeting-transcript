from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
from dotenv import load_dotenv
from flask_session import Session
import msal
import base64
import json

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

# Session cookie configuration for OAuth redirects
# These settings ensure session cookies persist during OAuth redirects to Microsoft
app.config['SESSION_COOKIE_NAME'] = 'flask_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access (security)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cookies during OAuth redirects
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

Session(app)

# Configuration
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
BYPASS_STATE_CHECK = os.getenv('BYPASS_STATE_CHECK', 'false').lower() == 'true'

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
    
    # Debug: Log session information
    print(f"DEBUG /auth/login: Generated state: {state}")
    print(f"DEBUG /auth/login: Session ID: {request.cookies.get('session')}")
    print(f"DEBUG /auth/login: Session contents: {dict(session)}")
    
    # Check if we need to return to a specific page after login
    return_type = request.args.get('return_type')
    return_id = request.args.get('return_id')
    return_email = request.args.get('email', '')
    
    if return_type and return_id:
        session['returnToSummary'] = {
            'type': return_type,
            'id': return_id,
            'email': return_email
        }
        print(f"DEBUG /auth/login: Set returnToSummary = {session['returnToSummary']}")
        
        # WORKAROUND: Also encode in state parameter as backup
        # This ensures we can recover the return URL even if session is lost
        # Use base64 encoding to make it URL-safe
        return_data = {
            'uuid': state,
            'type': return_type,
            'id': return_id,
            'email': return_email
        }
        return_json = json.dumps(return_data)
        state_with_return = base64.urlsafe_b64encode(return_json.encode()).decode()
        session["state"] = state
        session["encoded_state"] = state_with_return
        print(f"DEBUG /auth/login: Encoded return info in state for session recovery")
        print(f"DEBUG /auth/login: Using base64 encoded state: {state_with_return[:20]}...")
    else:
        print(f"DEBUG /auth/login: No return_type/return_id provided (return_type={return_type}, return_id={return_id})")
        session["encoded_state"] = None
    
    # Get authorization URL - always use the clean UUID state
    # The encoded state is stored in session for recovery
    auth_url = auth_service.get_login_url(state=state)
    print(f"DEBUG /auth/login: Redirecting to: {auth_url[:100]}...")
    
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
        meeting_type = summary_data['type']
        meeting_id = summary_data['id']
        
        # Construct proper route URL
        if meeting_type == 'teams':
            email = session.get('email', 'user@example.com')
            redirect_url = f"/teams/meeting/{meeting_id}/summary?email={email}"
        else:
            redirect_url = f"/zoom/meeting/{meeting_id}/summary"
    
    return jsonify({'success': True, 'redirect': redirect_url})


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Microsoft"""
    if USE_MOCK_DATA:
        return redirect(url_for('auth_mock_login'))
    
    # Debug: Log state information
    received_state = request.args.get('state')
    session_state = session.get("state")
    encoded_state = session.get("encoded_state")
    print(f"DEBUG: Received state: {received_state}")
    print(f"DEBUG: Session state: {session_state}")
    print(f"DEBUG: Encoded state in session: {encoded_state[:20] if encoded_state else None}...")
    print(f"DEBUG: Session ID: {request.cookies.get('session')}")
    print(f"DEBUG: Session contents: {dict(session)}")
    print(f"DEBUG: BYPASS_STATE_CHECK: {BYPASS_STATE_CHECK}")
    
    # State is now a clean UUID - no need to parse
    received_base_state = received_state
    session_base_state = session_state
    
    # Verify state to prevent CSRF (unless bypassed for debugging)
    if not BYPASS_STATE_CHECK and received_base_state != session_base_state:
        error_msg = f"State mismatch error. Received: {received_base_state}, Expected: {session_base_state}"
        print(f"ERROR: {error_msg}")
        print(f"\nTROUBLESHOOTING:")
        print(f"1. Session cookie may have been lost during OAuth redirect")
        print(f"2. Check that you're using consistent URLs (localhost vs 127.0.0.1)")
        print(f"3. Check browser cookies (F12 → Application → Cookies)")
        print(f"4. To bypass this check temporarily (DEBUG ONLY), set BYPASS_STATE_CHECK=true in .env")
        return f"Authentication error: {error_msg}<br><br>This usually means the session was lost. Try again and ensure you're using the same URL (localhost vs 127.0.0.1).", 400
    
    if BYPASS_STATE_CHECK:
        print(f"⚠️  WARNING: State check bypassed! This is a security risk - only use for debugging!")
        print(f"⚠️  Please fix your session cookie configuration and set BYPASS_STATE_CHECK=false")
    
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
            print(f"DEBUG /auth/callback: Checking returnToSummary in session...")
            print(f"DEBUG /auth/callback: returnToSummary = {session.get('returnToSummary')}")
            
            # Try to get return info from session first
            return_info = session.get('returnToSummary')
            
            # If not in session, try to recover from encoded_state (session loss workaround)
            if not return_info and encoded_state:
                try:
                    print(f"DEBUG /auth/callback: returnToSummary not in session, recovering from encoded state")
                    decoded_json = base64.urlsafe_b64decode(encoded_state.encode()).decode()
                    return_data = json.loads(decoded_json)
                    return_info = {
                        'type': return_data.get('type'),
                        'id': return_data.get('id'),
                        'email': return_data.get('email', '')
                    }
                    print(f"DEBUG /auth/callback: Recovered returnToSummary = {return_info}")
                except Exception as e:
                    print(f"ERROR /auth/callback: Failed to decode encoded_state: {e}")
            
            if return_info:
                meeting_type = return_info['type']
                meeting_id = return_info['id']
                
                # Remove from session if it was there
                if 'returnToSummary' in session:
                    session.pop('returnToSummary')
                if 'encoded_state' in session:
                    session.pop('encoded_state')
                
                print(f"DEBUG /auth/callback: Redirecting to summary page: type={meeting_type}, id={meeting_id}")
                
                # Construct proper route URL
                if meeting_type == 'teams':
                    email = return_info.get('email') or session.get('email') or user_profile.get('mail', 'user@example.com')
                    redirect_url = f"/teams/meeting/{meeting_id}/summary?email={email}"
                    print(f"DEBUG /auth/callback: Teams redirect URL: {redirect_url}")
                    return redirect(redirect_url)
                else:
                    redirect_url = f"/zoom/meeting/{meeting_id}/summary"
                    print(f"DEBUG /auth/callback: Zoom redirect URL: {redirect_url}")
                    return redirect(redirect_url)
            
            print(f"DEBUG /auth/callback: No returnToSummary found, redirecting to home")
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


@app.route('/debug/session')
def debug_session():
    """Debug endpoint to check session state"""
    if not app.debug:
        return "Debug endpoint only available in debug mode", 403
    
    return jsonify({
        'session_data': dict(session),
        'is_authenticated': _is_authenticated(),
        'use_mock_data': USE_MOCK_DATA,
        'session_id': request.cookies.get('session')
    })


@app.route('/debug/msal-config')
def debug_msal_config():
    """Debug MSAL configuration"""
    if not app.debug:
        return "Debug endpoint only available in debug mode", 403
    
    return jsonify({
        'use_mock_data': USE_MOCK_DATA,
        'client_id': auth_service.client_id[:10] + '...' if auth_service.client_id else 'NOT SET',
        'client_secret_set': bool(auth_service.client_secret),
        'client_secret_length': len(auth_service.client_secret) if auth_service.client_secret else 0,
        'authority': auth_service.authority,
        'redirect_uri': auth_service.redirect_uri,
        'scopes': auth_service.scopes
    })


# Routes
@app.route('/')
def home():
    """Home page with email input and meeting type buttons"""
    return render_template('home.html', 
                         authenticated=_is_authenticated(),
                         user=session.get('user'))


@app.route('/list/zoom/meetings', methods=['POST'])
def list_zoom_meetings():
    """Get list of Zoom meetings for a user and render meetings template"""
    try:
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
        else:
            email = request.form.get('email')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
        if not email:
            # Render home with an error message if email missing
            return render_template('home.html', error='Email is required'), 400
        
        if not start_date or not end_date:
            return render_template('home.html', error='Start date and end date are required'), 400

        # Use Zoom service to get recordings
        # Note: Date filtering will be added to the service later
        recordings = zoom_service.list_recordings(email)

        # Render meetings template with server-side data
        return render_template('meetings.html', meetings=recordings, email=email, meetingType='zoom', start_date=start_date, end_date=end_date)

    except Exception as e:
        return render_template('home.html', error=str(e)), 500


@app.route('/zoom/meeting/<meeting_id>/summary', methods=['GET'])
def get_zoom_meeting_summary(meeting_id):
    """Get transcript and summary for a Zoom meeting and render summary template"""
    try:
        # Check if we already have this summary cached in session
        cache_key = f'summary_zoom_{meeting_id}'
        cached_data = session.get(cache_key)
        
        if cached_data:
            print(f"DEBUG: Using cached summary for Zoom meeting {meeting_id}")
            return render_template('summary.html', 
                                 meeting_id=cached_data['meeting_id'],
                                 transcript=cached_data['transcript'],
                                 summary=cached_data['summary'],
                                 participants=cached_data['participants'],
                                 meetingType='zoom',
                                 authenticated=_is_authenticated(),
                                 user=session.get('user'),
                                 cached=True)
        
        # Get transcript from Zoom service
        transcript = zoom_service.get_meeting_transcript(meeting_id)

        # Generate summary using LLM service (expensive operation)
        print(f"DEBUG: Generating NEW summary for Zoom meeting {meeting_id}")
        summary = llm_service.generate_summary(transcript)

        # Mock participants for Zoom meetings (in real scenario, fetch from Zoom API)
        participants = [
            {"email": "participant1@example.com", "name": "Alice Johnson"},
            {"email": "participant2@example.com", "name": "Bob Smith"},
            {"email": "participant3@example.com", "name": "Carol Williams"}
        ]

        # Cache the result in session
        session[cache_key] = {
            'meeting_id': meeting_id,
            'transcript': transcript,
            'summary': summary,
            'participants': participants
        }

        return render_template('summary.html', 
                             meeting_id=meeting_id, 
                             transcript=transcript, 
                             summary=summary, 
                             participants=participants, 
                             meetingType='zoom',
                             authenticated=_is_authenticated(),
                             user=session.get('user'),
                             cached=False)

    except Exception as e:
        return render_template('meetings.html', error=str(e)), 500


@app.route('/list/teams/meetings', methods=['POST'])
def list_teams_meetings():
    """Get list of Teams meetings for a user and render meetings template"""
    try:
        # No authentication required - using application permissions
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
        else:
            email = request.form.get('email')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            
        if not email:
            return render_template('home.html', error='Email is required'), 400
        
        if not start_date or not end_date:
            return render_template('home.html', error='Start date and end date are required'), 400

        # Use Graph service with APPLICATION permissions (no user token needed)
        # Note: Date filtering will be added to the service later
        meetings = graph_service.list_meetings(email)

        return render_template('meetings.html', meetings=meetings, email=email, meetingType='teams', start_date=start_date, end_date=end_date)

    except Exception as e:
        return render_template('home.html', error=str(e)), 500


@app.route('/teams/meeting/<meeting_id>/summary', methods=['GET'])
def get_teams_meeting_summary(meeting_id):
    """Get transcript and summary for a Teams meeting and render summary template"""
    try:
        # Debug logging
        print(f"DEBUG: /teams/meeting/{meeting_id}/summary called")
        print(f"DEBUG: Query params: {dict(request.args)}")
        print(f"DEBUG: Authenticated: {_is_authenticated()}")
        
        # No authentication required for viewing - using application permissions
        # Get email from query parameter
        email = request.args.get('email', 'user@example.com')
        
        # Check if we already have this summary cached in session
        cache_key = f'summary_{meeting_id}'
        cached_data = session.get(cache_key)
        
        if cached_data:
            print(f"DEBUG: Using cached summary for meeting {meeting_id}")
            return render_template('summary.html', 
                                 meeting_id=cached_data['meeting_id'],
                                 transcript=cached_data['transcript'],
                                 summary=cached_data['summary'],
                                 participants=cached_data['participants'],
                                 meetingType='teams',
                                 authenticated=_is_authenticated(),
                                 user=session.get('user'),
                                 email=email,
                                 cached=True)
        
        # Get transcript and participants from Graph service using APPLICATION permissions
        transcript, participants = graph_service.get_meeting_transcript(meeting_id, email)

        # Generate summary using LLM service (expensive operation)
        print(f"DEBUG: Generating NEW summary for meeting {meeting_id}")
        summary = llm_service.generate_summary(transcript)

        # Cache the result in session (survives OAuth redirects)
        session[cache_key] = {
            'meeting_id': meeting_id,
            'transcript': transcript,
            'summary': summary,
            'participants': participants
        }

        return render_template('summary.html', 
                             meeting_id=meeting_id, 
                             transcript=transcript, 
                             summary=summary, 
                             participants=participants, 
                             meetingType='teams',
                             authenticated=_is_authenticated(),
                             user=session.get('user'),
                             email=email,
                             cached=False)

    except Exception as e:
        return render_template('meetings.html', error=str(e)), 500


@app.route('/teams/send-summary', methods=['POST'])
def send_summary_to_teams():
    """Create Teams chat and send summary to participants"""
    # Determine request type early for error handling
    is_json_request = request.is_json or request.content_type == 'application/json'
    
    try:
        # Check authentication for Teams
        if not _is_authenticated():
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Handle both form data and JSON
        if is_json_request:
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
            if is_json_request:
                return jsonify({'error': 'Meeting ID and summary are required'}), 400
            else:
                return render_template('summary.html', error='Meeting ID and summary are required'), 400

        # Get access token
        access_token = _get_token_from_cache()
        if not access_token and USE_MOCK_DATA:
            access_token = session.get('access_token', 'mock_token')
        
        if not access_token:
            return jsonify({'error': 'No valid access token'}), 401

        # Use Graph service to send chat message with access token
        result = graph_service.send_chat_message(meeting_id, summary, participants, access_token)

        # Return appropriate response based on request type
        if isinstance(result, dict) and result.get('success'):
            if is_json_request:
                # Return JSON response for fetch requests
                return jsonify(result)
            else:
                # Return HTML for form submissions
                return render_template('summary.html', 
                                     meeting_id=meeting_id, 
                                     transcript=None, 
                                     summary=summary, 
                                     participants=participants, 
                                     message=result.get('message', 'Summary sent'), 
                                     meetingType='teams',
                                     authenticated=_is_authenticated(),
                                     user=session.get('user'))
        else:
            if is_json_request:
                return jsonify({'error': str(result)}), 500
            else:
                return render_template('summary.html', error=str(result)), 500

    except Exception as e:
        import traceback
        print(f"Error in send_summary_to_teams: {e}")
        print(traceback.format_exc())
        
        if is_json_request:
            return jsonify({'error': str(e)}), 500
        else:
            return render_template('summary.html', error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
