# Access Token Flow - Delegated Permissions

## Overview
This document explains how Microsoft access tokens are saved and used in the transcript-summary-delegated app.

## Token Storage Location

### 1. **MSAL Token Cache (Primary Storage)**
- **Location**: Flask server-side session (`session["token_cache"]`)
- **Format**: Serialized `msal.SerializableTokenCache` object
- **Lifecycle**: Persists across requests for the same user session
- **Contains**: 
  - Access tokens
  - Refresh tokens
  - Token expiration times
  - Account information

### 2. **Helper Functions** (in `app.py`)

#### `_load_cache()`
```python
def _load_cache():
    """Load token cache from session"""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache
```
Retrieves the serialized token cache from Flask session and deserializes it.

#### `_save_cache(cache)`
```python
def _save_cache(cache):
    """Save token cache to session"""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
```
Saves the token cache back to Flask session if it has changed (e.g., token refreshed).

#### `_get_token_from_cache()`
```python
def _get_token_from_cache():
    """Get valid access token from cache or refresh if needed"""
    cache = _load_cache()
    accounts = auth_service.get_accounts(cache=cache)
    
    if accounts:
        # Try to acquire token silently (uses refresh token if needed)
        result = auth_service.acquire_token_silent(
            account=accounts[0],
            cache=cache
        )
        
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]
    
    return None
```
Gets a valid access token from cache, automatically refreshing it using the refresh token if expired.

## Token Acquisition Flow

### Initial Login (Authorization Code Flow)
1. User clicks "Sign in with Microsoft"
2. Redirected to `/auth/login`
3. App generates auth URL via `auth_service.get_login_url()`
4. User redirected to Microsoft login page
5. User consents to permissions
6. Microsoft redirects back to `/auth/callback` with authorization code
7. App exchanges code for tokens via `auth_service.acquire_token_by_auth_code()`
8. Tokens saved to cache via `_save_cache()`

### Subsequent Requests (Silent Token Acquisition)
1. App calls `_get_token_from_cache()`
2. MSAL checks if cached token is still valid
3. If valid: Returns cached access token
4. If expired: Uses refresh token to get new access token automatically
5. Updates cache with new tokens

## Where Access Tokens Are Used

### 1. **Microsoft Graph API Calls** (`services/graph_service.py`)

All Graph API calls require the user's access token:

```python
def _make_api_call(self, endpoint, access_token, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Makes authenticated API call
```

#### Functions Using Access Token:
- `get_user_profile(access_token)` - Get user's Microsoft profile
- `list_meetings(access_token)` - List Teams meetings
- `get_meeting_transcript(meeting_id, access_token)` - Get meeting transcript
- `send_chat_message(meeting_id, summary, participants, access_token)` - Send summary to Teams

### 2. **Flask Routes** (`app.py`)

Routes that require authentication pass the token to Graph service:

#### `/list/teams/meetings`
```python
access_token = _get_token_from_cache()
meetings = graph_service.list_meetings(access_token)
```

#### `/teams/meeting/<meeting_id>/summary`
```python
access_token = _get_token_from_cache()
transcript, participants = graph_service.get_meeting_transcript(meeting_id, access_token)
```

#### `/teams/send-summary`
```python
access_token = _get_token_from_cache()
result = graph_service.send_chat_message(meeting_id, summary, participants, access_token)
```

## Zoom vs Teams: Token Requirements

### Zoom Meetings
- ❌ **Does NOT require Microsoft access token**
- ✅ Uses Zoom API credentials (not implemented in delegated version)
- ✅ Can be accessed without signing in
- Routes: `/list/zoom/meetings`, `/zoom/meeting/<id>/summary`

### Teams Meetings
- ✅ **REQUIRES Microsoft access token** (delegated permissions)
- ✅ User must sign in with Microsoft account
- ✅ Token automatically refreshed when expired
- Routes: `/list/teams/meetings`, `/teams/meeting/<id>/summary`, `/teams/send-summary`

## Security Features

1. **Server-side Sessions**: Tokens never exposed to client JavaScript
2. **Automatic Refresh**: Expired tokens automatically renewed using refresh tokens
3. **CSRF Protection**: State parameter validates OAuth callback
4. **HTTPS Required**: Production should use HTTPS to protect tokens in transit
5. **Token Scoping**: Only requests minimum permissions needed (User.Read, OnlineMeetings.Read, Chat.Create)

## Mock Mode

When `USE_MOCK_DATA=true`:
- Tokens are not sent to real Microsoft servers
- Mock tokens stored as: `session["access_token"] = "mock_token"`
- No actual OAuth flow occurs
- Used for testing without Microsoft credentials

## Token Lifecycle

```
Login → Authorization Code → Access Token + Refresh Token → Cache
                                     ↓
                              Used for API calls
                                     ↓
                               Token expires?
                                     ↓
                           Yes: Use refresh token
                                     ↓
                           New access token → Cache
```

## Key Permissions Required

Defined in `services/auth_service.py`:
- `User.Read` - Read user profile
- `OnlineMeetings.Read` - Read Teams meetings  
- `Chat.Create` - Create Teams chats (for sending summaries)
- `offline_access` - Get refresh tokens for long-term access
