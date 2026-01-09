# Hybrid Authentication Flow - Application + Delegated Permissions

## Overview
This application uses a **hybrid permission model**:
- **Application Permissions** for reading data (meetings, transcripts) - NO user login required
- **Delegated Permissions** ONLY for posting messages to Teams - requires user login

## Why Hybrid Permissions?

### Application Permissions (for Reading)
- **No User Login Required**: Users can view meetings and transcripts without authentication
- **Better UX**: Faster access to data, no login friction
- **Appropriate Use**: Reading meeting data doesn't require user context
- **Permissions Needed**: `Calendars.Read`, `OnlineMeetings.Read` (application-level)

### Delegated Permissions (for Posting)
- **Required by Microsoft**: Creating group chats and sending messages REQUIRES delegated permissions
- **User Context**: Messages are sent as the authenticated user, not as the app
- **Security**: Users explicitly consent to the app posting on their behalf
- **Permissions Needed**: `Chat.ReadWrite`, `ChatMessage.Send` (delegated)

## Permission Comparison

| Operation | Permission Type | Login Required | Why |
|-----------|----------------|----------------|-----|
| List Teams Meetings | Application | ❌ No | Admin access to read organizational data |
| Get Meeting Transcript | Application | ❌ No | Admin access to read organizational data |
| Generate AI Summary | None | ❌ No | Local processing only |
| Send to Teams Chat | Delegated | ✅ Yes | Must act as specific user to post messages |

## Flow Details

### 1. Viewing Meetings & Transcripts (No Auth)
```
User enters email → Fetch meetings with APP token → Display list
   ↓
Click meeting → Fetch transcript with APP token → Generate summary → Display
```
**No user authentication required!**

### 2. Posting to Teams (Auth Required)
```
User clicks "Login to Post in Teams"
   ↓
Redirect to Microsoft login → User consents → Get delegated token
   ↓
Click "Send in Teams" → Create chat with USER token → Post message
```

## Authentication Flow

### Viewing Data (No Login Required)
1. User enters email and selects "Get Teams Meetings"
2. App uses **application token** (client credentials) to fetch meetings
3. Meetings are displayed
4. User clicks on a meeting
5. App uses **application token** to fetch transcript and participants
6. LLM generates summary and displays it

**No user interaction for authentication!**

### Posting to Teams (Login Required)

#### Mock Mode (for testing):
1. User clicks "Login to Post in Teams"
2. Redirected to `/auth/mock-login`
3. Shows mock consent screen with permissions
4. User clicks "Accept & Sign In"
5. Mock delegated token is created and stored in session
6. User is redirected back to summary page
7. Button changes to "Send in Teams"
8. User clicks "Send in Teams"
9. App uses **delegated token** to create chat and post message

#### Production Mode:
1. User clicks "Login to Post in Teams"
2. App generates state token for CSRF protection
3. User is redirected to Microsoft's login page
4. User enters credentials and consents to **delegated** permissions
5. Microsoft redirects back to `/auth/callback` with authorization code
6. App exchanges code for **delegated** access token using MSAL
7. User profile is fetched and stored in session
8. User is redirected back to summary page
9. Button changes to "Send in Teams"
10. User clicks "Send in Teams"
11. App uses **delegated token** to create chat and post message

## Token Management

### Application Token (for Reading)
- Acquired automatically by `graph_service._get_access_token()`
- Uses **client credentials flow** (no user interaction)
- Stored temporarily for API calls
- Short-lived, automatically refreshed as needed

### Delegated Token (for Posting)
- Acquired only when user clicks "Login to Post in Teams"
- Stored in server-side session (Flask-Session with filesystem backend)
- MSAL handles token caching and refresh automatically
- `_get_token_from_cache()` retrieves valid tokens or refreshes them silently

## API Calls

### Reading Data (Application Permissions)
- `graph_service.list_meetings(email)` - Uses app token to get meetings for any user
- `graph_service.get_meeting_transcript(meeting_id, email)` - Uses app token to get transcript

### Posting Data (Delegated Permissions)
- `graph_service.send_chat_message(meeting_id, summary, participants, access_token)` - Uses **delegated** token to send as logged-in user

## Button Logic in Summary Page

### For Zoom Meetings
- No "Send in Teams" button shown (Zoom doesn't integrate with Teams chat)
- Only Edit/Save buttons available

### For Teams Meetings - Not Authenticated
```html
<button onclick="loginToSend()">🔐 Login to Post in Teams</button>
```
- Stores pending summary data in sessionStorage
- Redirects to `/auth/login`
- After login, button changes and summary can be sent

### For Teams Meetings - Authenticated
```html
<button onclick="sendToTeams()">📤 Send in Teams</button>
```
- Directly sends summary using stored delegated token
- No redirect needed

## Required Permissions

### Application Permissions (Azure AD App Registration)
For reading organizational data without user consent:
- `Calendars.Read` - Read calendar events across the organization
- `OnlineMeetings.Read` - Read online meeting details
- ⚠️ **Requires Admin Consent** in Azure AD

### Delegated Permissions (User Consent)
For acting on behalf of signed-in user:
- `User.Read` - Read user profile (standard)
- `Chat.ReadWrite` - Read and write user's chats
- `ChatMessage.Send` - Send chat messages as the user
- ✅ **User consents** during login flow

## Session Data

The app stores in session:
- `authenticated` (bool) - Whether user is authenticated (mock mode)
- `access_token` (str) - Access token (mock mode)
- `token_cache` (str) - Serialized MSAL token cache (production mode)
- `user` (dict) - User profile info (name, email)
- `returnToSummary` (dict) - Return destination after login

## Environment Variables

Required for production (both permission types):
```bash
# Azure AD App Registration
MICROSOFT_CLIENT_ID=<your-app-client-id>
MICROSOFT_CLIENT_SECRET=<your-app-client-secret>
MICROSOFT_TENANT_ID=<your-tenant-id>
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback

# Feature flags
USE_MOCK_DATA=false
```

For testing with mock data:
```bash
USE_MOCK_DATA=true
```

## Flow Diagrams

### Reading Data (Application Permissions - No Login)
```
User enters email → "Get Teams Meetings"
    ↓
App gets APPLICATION token (client credentials)
    ↓
Call Graph API: /users/{email}/onlineMeetings
    ↓
Display meetings → User clicks meeting
    ↓
App uses same APPLICATION token
    ↓
Call Graph API: /users/{email}/onlineMeetings/{id}/transcript
    ↓
Generate summary with LLM → Display
```

### Posting to Teams (Delegated Permissions - Login Required)
```
User clicks "Login to Post in Teams"
    ↓
Redirect to Microsoft login (OAuth 2.0)
    ↓
User consents to DELEGATED permissions
    ↓
App receives authorization code
    ↓
Exchange code for DELEGATED access token
    ↓
Store token in session → Return to summary page
    ↓
Button changes to "Send in Teams"
    ↓
User clicks → App uses DELEGATED token
    ↓
Call Graph API: POST /chats (create group chat)
    ↓
Call Graph API: POST /chats/{id}/messages (send summary)
    ↓
Success ✅
```

## Testing the Hybrid Flow

1. **Start the app**: `python app.py`
2. **Test reading** (no auth):
   - Visit http://localhost:5001
   - Enter any email
   - Click "Get Teams Meetings"
   - ✅ Meetings load WITHOUT login
   - Click on a meeting
   - ✅ Transcript and summary load WITHOUT login

3. **Test posting** (requires auth):
   - On summary page, click "Login to Post in Teams"
   - ✅ Redirected to mock login page
   - Click "Accept & Sign In"
   - ✅ Returned to summary, button now says "Send in Teams"
   - Click "Send in Teams"
   - ✅ Summary posted successfully

## Production Setup

### 1. Register App in Azure AD
- Go to Azure Portal → Azure Active Directory → App Registrations
- Create new registration
- Note down: Client ID, Tenant ID
- Create client secret, note it down

### 2. Configure Application Permissions
- In app registration, go to "API Permissions"
- Add permissions → Microsoft Graph → **Application permissions**:
  - ✅ `Calendars.Read`
  - ✅ `OnlineMeetings.Read`
- Click "Grant admin consent" (requires admin)

### 3. Configure Delegated Permissions
- Add permissions → Microsoft Graph → **Delegated permissions**:
  - ✅ `User.Read` (should already be there)
  - ✅ `Chat.ReadWrite`
  - ✅ `ChatMessage.Send`
- No admin consent needed (users consent during login)

### 4. Configure Redirect URI
- In app registration, go to "Authentication"
- Add platform → Web
- Redirect URI: `http://localhost:5001/auth/callback` (or your domain)

### 5. Update Environment Variables
```bash
MICROSOFT_CLIENT_ID=<from-step-1>
MICROSOFT_CLIENT_SECRET=<from-step-1>
MICROSOFT_TENANT_ID=<from-step-1>
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback
USE_MOCK_DATA=false
```

### 6. Deploy and Test!

## Security Notes

- ✅ Application token never leaves the server
- ✅ Delegated token stored in server-side session (not exposed to client)
- ✅ CSRF protection using state parameter in OAuth flow
- ✅ Token refresh handled automatically by MSAL
- ✅ Principle of least privilege: Only use delegated permissions where absolutely required

## Key Benefits of This Approach

1. **Better UX**: Users can view data without logging in
2. **Scalability**: Application token can access any user's data (with admin consent)
3. **Security**: User login only required when posting messages
4. **Compliance**: Clear separation between reading (admin) and writing (user) operations
5. **Flexibility**: Easy to add features that don't require user context

## Troubleshooting

### "Access denied" when fetching meetings
- Ensure application permissions are granted admin consent in Azure AD

### "Insufficient privileges" when posting to Teams
- Ensure user has consented to delegated permissions
- Check that delegated permissions are correctly configured

### Login loop or session issues
- Clear browser cookies and session data
- Check that SESSION_TYPE is configured correctly
- Ensure flask-session is installed
