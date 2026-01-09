# OAuth Redirect URI Configuration Guide

## Overview
This document explains how OAuth redirect URIs work in both **mock mode (development)** and **production with Microsoft Entra ID**.

---

## Current Configuration

### Where Redirect URI is Set

#### 1. **Environment Variable** (`.env` file)
```bash
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback
```

#### 2. **Auth Service** (`services/auth_service.py`)
```python
self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:5001/auth/callback')
```

The redirect URI is read from the environment variable, with a fallback default value.

---

## How OAuth Redirect Works

### The OAuth 2.0 Authorization Code Flow

```
User Browser          Your App              Microsoft Entra ID
     |                   |                        |
     |  1. Click Login   |                        |
     |------------------>|                        |
     |                   |                        |
     |                   | 2. Redirect to MS Login|
     |                   |----------------------->|
     |                                            |
     |  3. User enters credentials                |
     |<-------------------------------------------|
     |  4. User consents to permissions           |
     |                                            |
     |  5. MS redirects back with auth code       |
     |<-------------------------------------------|
     | http://yourapp/auth/callback?code=ABC123   |
     |                   |                        |
     |  6. Send to app   |                        |
     |------------------>|                        |
     |                   |                        |
     |                   | 7. Exchange code for token
     |                   |----------------------->|
     |                   |                        |
     |                   | 8. Return access token |
     |                   |<-----------------------|
     |                   |                        |
     |  9. Redirect to   |                        |
     |    summary page   |                        |
     |<------------------|                        |
```

### Key Points:
- **Step 2**: Your app redirects to Microsoft with `redirect_uri` parameter
- **Step 5**: Microsoft redirects back to **exactly** that URI with auth code
- **Step 6**: Your `/auth/callback` endpoint handles the code
- **Step 7-8**: Your app exchanges code for access token
- **Step 9**: Your app redirects user to final destination

---

## Mock Mode (Current Development Setup)

### Flow in Mock Mode
When `USE_MOCK_DATA=true`:

1. **User clicks "Login to Post in Teams"**
   ```javascript
   window.location.href = '/auth/login?return_type=teams&return_id=123';
   ```

2. **`/auth/login` route** (app.py)
   ```python
   @app.route('/auth/login')
   def auth_login():
       session['returnToSummary'] = {'type': 'teams', 'id': '123'}
       auth_url = auth_service.get_login_url(state=state)
       return redirect(auth_url)
   ```

3. **Mock auth service** returns mock login URL
   ```python
   def get_login_url(self, state=None):
       if self.use_mock:
           return url_for('auth_mock_login', _external=True)
       # Real MS login URL...
   ```
   Returns: `http://localhost:5001/auth/mock-login`

4. **Mock login page** (`templates/mock_login.html`)
   - User clicks "Accept & Sign In"
   - Submits to `/auth/mock-callback`

5. **`/auth/mock-callback` route** (app.py)
   ```python
   @app.route('/auth/mock-callback', methods=['POST'])
   def auth_mock_callback():
       session["authenticated"] = True
       session["user"] = {"name": "Mock User", "email": "user@example.com"}
       session["access_token"] = "mock_access_token_delegated"
       
       # Get stored return info
       if session.get('returnToSummary'):
           summary_data = session.pop('returnToSummary')
           redirect_url = f"/teams/meeting/{summary_data['id']}/summary?email=..."
       
       return jsonify({'success': True, 'redirect': redirect_url})
   ```

6. **Frontend redirects** to summary page
   ```javascript
   window.location.href = data.redirect;
   ```

### Redirect URI in Mock Mode
- **Not actually used** - we bypass Microsoft and use internal routes
- **Purpose**: Just for configuration consistency
- **Value**: `http://localhost:5001/auth/callback` (unused in mock)

---

## Production Mode (Real Microsoft Entra ID)

### Prerequisites

#### 1. Register App in Microsoft Entra ID
Go to [Azure Portal](https://portal.azure.com) → **Azure Active Directory** → **App registrations**

**Create new registration:**
- **Name**: Meeting Transcript Summary App
- **Supported account types**: 
  - "Accounts in this organizational directory only" (Single tenant)
  - OR "Accounts in any organizational directory" (Multi-tenant)
- **Redirect URI**: 
  - Platform: **Web**
  - URI: Your app's callback URL

#### 2. Configure Redirect URIs

**Development:**
```
http://localhost:5001/auth/callback
```

**Production:**
```
https://yourdomain.com/auth/callback
```

**Important:** You can add multiple redirect URIs for different environments!

Example configuration in Azure:
```
✓ http://localhost:5001/auth/callback       (Development)
✓ https://staging.yourapp.com/auth/callback (Staging)
✓ https://yourapp.com/auth/callback         (Production)
```

#### 3. Configure Permissions

**API Permissions** → **Add a permission** → **Microsoft Graph**

**Delegated permissions** (user login required):
- `User.Read` - Read user profile
- `Calendars.Read` - Read user's calendar
- `OnlineMeetings.Read` - Read user's online meetings
- `Chat.ReadWrite` - Read and write chats
- `ChatMessage.Send` - Send chat messages

**Application permissions** (no user login - for reading):
- `Calendars.Read` - Read all calendars
- `OnlineMeetings.Read.All` - Read all online meetings
- `User.Read.All` - Read all user profiles

Click **Grant admin consent** for your organization.

#### 4. Create Client Secret

**Certificates & secrets** → **New client secret**
- Description: "Meeting Transcript App Secret"
- Expires: Choose appropriate expiration
- **Copy the secret value immediately** (won't be shown again!)

---

### Production Flow

When `USE_MOCK_DATA=false`:

1. **User clicks "Login to Post in Teams"**
   ```javascript
   window.location.href = '/auth/login?return_type=teams&return_id=123';
   ```

2. **`/auth/login` route** stores return info and gets MS login URL
   ```python
   @app.route('/auth/login')
   def auth_login():
       state = str(uuid.uuid4())
       session["state"] = state
       session['returnToSummary'] = {'type': 'teams', 'id': '123'}
       
       auth_url = auth_service.get_login_url(state=state)
       # Returns Microsoft login URL
       
       return redirect(auth_url)
   ```

3. **Auth service builds Microsoft login URL**
   ```python
   def get_login_url(self, state=None):
       auth_url = msal_app.get_authorization_request_url(
           scopes=["User.Read", "Chat.ReadWrite", ...],
           state=state,
           redirect_uri=self.redirect_uri  # YOUR CALLBACK URL
       )
       return auth_url
   ```
   
   Returns something like:
   ```
   https://login.microsoftonline.com/[tenant]/oauth2/v2.0/authorize
   ?client_id=[your-client-id]
   &response_type=code
   &redirect_uri=https://yourapp.com/auth/callback
   &scope=User.Read+Chat.ReadWrite
   &state=abc-123-xyz
   ```

4. **User is redirected to Microsoft login page**
   - User enters Microsoft credentials
   - User sees consent screen with requested permissions
   - User clicks "Accept"

5. **Microsoft redirects back to your app**
   ```
   https://yourapp.com/auth/callback
   ?code=0.AXsA7tK...long-auth-code...
   &state=abc-123-xyz
   ```

6. **`/auth/callback` route** handles the response
   ```python
   @app.route('/auth/callback')
   def auth_callback():
       # Verify state matches (CSRF protection)
       if request.args.get('state') != session.get("state"):
           return "State mismatch error", 400
       
       # Get the authorization code
       auth_code = request.args['code']
       
       # Exchange code for access token
       cache = _load_cache()
       result = auth_service.acquire_token_by_auth_code(
           auth_code=auth_code,
           cache=cache
       )
       
       if "access_token" in result:
           _save_cache(cache)
           
           # Get user profile
           user_profile = graph_service.get_user_profile(result["access_token"])
           session["user"] = {
               "name": user_profile.get("displayName"),
               "email": user_profile.get("mail")
           }
           
           # Redirect to original destination
           if session.get('returnToSummary'):
               summary_data = session.pop('returnToSummary')
               return redirect(f"/teams/meeting/{summary_data['id']}/summary")
           
           return redirect(url_for('home'))
   ```

7. **User ends up on summary page, authenticated**
   - Session contains user info and access token
   - `authenticated=True` in template
   - "📤 Send in Teams" button is shown

---

## Environment Configuration

### Development (.env file)
```bash
USE_MOCK_DATA=false  # Switch to real Microsoft auth

# Your Azure App Registration details
MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MICROSOFT_CLIENT_SECRET=your-secret-value-here
MICROSOFT_TENANT_ID=your-tenant-id-here
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback

# Authority URL (tenant-specific or common)
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
# OR for multi-tenant:
# MICROSOFT_AUTHORITY=https://login.microsoftonline.com/common
```

### Production (.env file)
```bash
USE_MOCK_DATA=false

MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MICROSOFT_CLIENT_SECRET=your-production-secret
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_REDIRECT_URI=https://yourapp.com/auth/callback
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
```

---

## Redirect URI Must Match Exactly

### ⚠️ Critical Requirement

The redirect URI sent to Microsoft **MUST EXACTLY MATCH** one of the URIs registered in Azure Portal.

**Matching rules:**
- Protocol: `http` vs `https` - **must match**
- Domain: `localhost` vs `yourapp.com` - **must match**
- Port: `:5001` vs `:80` - **must match** (include if non-standard)
- Path: `/auth/callback` vs `/callback` - **must match**
- Trailing slash: `/auth/callback/` vs `/auth/callback` - **must match**

### Examples:

✅ **Correct:**
- Azure registered: `https://yourapp.com/auth/callback`
- .env configured: `MICROSOFT_REDIRECT_URI=https://yourapp.com/auth/callback`
- **Result**: Works!

❌ **Wrong:**
- Azure registered: `https://yourapp.com/auth/callback`
- .env configured: `MICROSOFT_REDIRECT_URI=http://yourapp.com/auth/callback`
- **Result**: Error - Protocol mismatch

❌ **Wrong:**
- Azure registered: `https://yourapp.com/auth/callback`
- .env configured: `MICROSOFT_REDIRECT_URI=https://yourapp.com/callback`
- **Result**: Error - Path mismatch

---

## Testing the Production Flow

### Step 1: Update .env
```bash
USE_MOCK_DATA=false
MICROSOFT_CLIENT_ID=your-real-client-id
MICROSOFT_CLIENT_SECRET=your-real-secret
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback
```

### Step 2: Register Redirect URI in Azure
- Go to your app registration
- **Authentication** → **Platform configurations** → **Web**
- Add `http://localhost:5001/auth/callback`
- Click **Save**

### Step 3: Test Login Flow
1. Start app: `./start_fresh.sh`
2. Navigate to Teams meeting summary
3. Click "🔐 Login to Post in Teams"
4. **You'll be redirected to real Microsoft login**
5. Enter your Microsoft credentials
6. Accept consent screen
7. **Redirected back to your app at** `http://localhost:5001/auth/callback?code=...`
8. App exchanges code for token
9. **You're redirected back to summary page**
10. See "📤 Send in Teams" button ✅

---

## Common Issues & Solutions

### Issue: "AADSTS50011: The reply URL specified in the request does not match"

**Cause:** Redirect URI mismatch

**Solution:**
1. Check exact URI in Azure Portal under **Authentication**
2. Ensure `.env` has **exactly** the same URI
3. Check for trailing slashes, http vs https, port numbers
4. Restart app after changing `.env`

### Issue: "AADSTS7000215: Invalid client secret provided"

**Cause:** Wrong or expired client secret

**Solution:**
1. Generate new client secret in Azure Portal
2. Update `MICROSOFT_CLIENT_SECRET` in `.env`
3. Restart app

### Issue: "Redirect URI shows error page instead of app"

**Cause:** Your `/auth/callback` route has an error

**Solution:**
1. Check Flask logs for errors
2. Verify route is registered: `flask routes | grep callback`
3. Test with debug mode: `FLASK_DEBUG=true`

### Issue: Session not persisting after redirect

**Cause:** Session cookie configuration

**Solution:**
1. Ensure `FLASK_SECRET_KEY` is set in `.env`
2. Check session type: `SESSION_TYPE=filesystem`
3. For production, use Redis or database sessions
4. Ensure cookies are allowed in browser

---

## Production Deployment Considerations

### 1. HTTPS Required
Microsoft requires HTTPS for production redirect URIs (except localhost).

**Azure Portal will show:**
```
⚠️ For production, redirect URIs must use HTTPS
✓ http://localhost:5001/auth/callback  (allowed for dev)
❌ http://yourapp.com/auth/callback    (not allowed)
✓ https://yourapp.com/auth/callback   (correct)
```

### 2. Domain Configuration
If deploying to:
- **Azure App Service**: `https://yourapp.azurewebsites.net/auth/callback`
- **Custom Domain**: `https://yourdomain.com/auth/callback`
- **Heroku**: `https://yourapp.herokuapp.com/auth/callback`
- **AWS**: `https://yourapp.elasticbeanstalk.com/auth/callback`

### 3. Environment Variables
Set these in your hosting platform:
- Azure App Service: **Configuration** → **Application settings**
- Heroku: `heroku config:set MICROSOFT_REDIRECT_URI=...`
- AWS: Elastic Beanstalk environment properties
- Docker: Environment variables in docker-compose or k8s

### 4. Session Storage
For production with multiple servers:

**Option 1: Redis**
```python
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
```

**Option 2: Database**
```python
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'
```

### 5. State Parameter Security
- Already implemented with UUID
- Consider adding expiration: store state with timestamp
- Clean up old states periodically

---

## Summary

### Current Setup (Mock Mode)
✅ **Works for development/testing**
- No actual Microsoft redirect
- Internal routes simulate OAuth
- Same-window flow ensures session persistence

### Production Setup (Real Microsoft)
✅ **Will work seamlessly with same code**
- Just change `USE_MOCK_DATA=false`
- Configure Azure app registration
- Update `.env` with real credentials
- Register correct redirect URI in Azure Portal
- **Same flow, same session handling, same redirect logic**

### The Key Insight
Your current authentication fix (same-window redirect) **works perfectly for both mock and production** because:
1. ✅ Session cookie is set in same browser context
2. ✅ Redirect preserves session throughout flow
3. ✅ No cross-window session issues
4. ✅ Standard OAuth pattern that Microsoft expects

**No code changes needed when moving to production!** 🎉
