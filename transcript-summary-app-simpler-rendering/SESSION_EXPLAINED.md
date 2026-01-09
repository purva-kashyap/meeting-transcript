# Flask Session Management Explained

## 🔍 Overview: How Flask Sessions Work

Flask sessions provide a way to store information about a user across requests. Think of it as a way to "remember" users between page visits.

---

## 📚 Your Application's Session Configuration

### Current Setup (in `app.py`)

```python
from flask_session import Session

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure server-side session
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
app.config['SESSION_PERMANENT'] = os.getenv('SESSION_PERMANENT', 'false').lower() == 'true'
Session(app)
```

### What This Means

1. **`SESSION_TYPE = 'filesystem'`** - Store session data as **physical files** on disk
2. **`SESSION_PERMANENT = false`** - Sessions expire when browser closes
3. **`Session(app)`** - Initialize Flask-Session extension

---

## 🗂️ Two Types of Sessions

### Default Flask Sessions (Built-in)
```python
# Without flask_session extension
session['user'] = 'John'
```
- ✅ **Storage**: Client-side (browser cookie)
- ⚠️ **Size limit**: 4KB max (cookie size limit)
- ⚠️ **Security**: Data is signed but visible to client
- ⚠️ **Problem**: Can't store large data like OAuth tokens

### Flask-Session (Server-side) - What You're Using
```python
# With flask_session extension
session['access_token'] = 'very_long_oauth_token...'
session['token_cache'] = {...}  # Large MSAL token cache
```
- ✅ **Storage**: Server-side (filesystem, Redis, database)
- ✅ **Size limit**: No practical limit
- ✅ **Security**: Data never leaves server
- ✅ **Perfect for**: OAuth tokens, user data, sensitive info

---

## 💾 Why Physical Files? (Filesystem Sessions)

### The Session Flow

```
1. User visits your app
   ↓
2. Flask creates a session file
   flask_session/2029240f6d1128be89ddc32729463129
   ↓
3. Flask sends a cookie to browser
   Set-Cookie: session=2029240f6d1128be89ddc32729463129
   ↓
4. Browser sends cookie with every request
   Cookie: session=2029240f6d1128be89ddc32729463129
   ↓
5. Flask reads the corresponding file
   flask_session/2029240f6d1128be89ddc32729463129
   ↓
6. Your code can access session data
   session['authenticated']
   session['access_token']
```

### What's in the Physical Files?

Let's look at an actual session file:

```bash
$ cat flask_session/2029240f6d1128be89ddc32729463129
```

Contains (serialized Python dictionary):
```python
{
    'authenticated': True,
    'user': {
        'name': 'Mock User',
        'email': 'user@example.com'
    },
    'access_token': 'mock_access_token_delegated',
    'token_cache': '{"AccessToken": {"secret": "...", "credential_type": "AccessToken", ...}}',
    'returnToSummary': None,
    'state': 'abc-123-xyz',
    'email': 'user@example.com'
}
```

### Why Physical Files Work for Development

**Advantages:**
- ✅ **Simple setup** - No additional infrastructure needed
- ✅ **Easy debugging** - Can inspect files directly
- ✅ **No dependencies** - No Redis/database required
- ✅ **Works locally** - Perfect for development
- ✅ **Persistent across app restarts** - Files remain until deleted

**Disadvantages:**
- ⚠️ **Not scalable** - Doesn't work with multiple servers
- ⚠️ **File I/O overhead** - Slower than memory-based storage
- ⚠️ **Cleanup required** - Old files accumulate (hence `start_fresh.sh`)
- ⚠️ **Single server only** - Load balancer would break it

---

## 🔐 How OAuth Tokens Are Saved

### The MSAL Token Cache Flow

Your application uses **MSAL (Microsoft Authentication Library)** which has its own token cache system.

### Step-by-Step: Token Storage

#### 1. **User Logs In** (`/auth/callback`)

```python
@app.route('/auth/callback')
def auth_callback():
    # Load existing cache from session (or create new)
    cache = _load_cache()
    
    # Exchange auth code for tokens
    result = auth_service.acquire_token_by_auth_code(
        auth_code=request.args['code'],
        cache=cache  # MSAL writes to this cache
    )
    
    # Save cache back to session
    _save_cache(cache)
    
    # Also save user info
    session["user"] = {...}
```

#### 2. **Loading Token Cache** (`_load_cache()`)

```python
def _load_cache():
    """Load token cache from session"""
    cache = msal.SerializableTokenCache()
    
    # Check if we have cached tokens in session
    if session.get("token_cache"):
        # Deserialize from session into MSAL cache object
        cache.deserialize(session["token_cache"])
    
    return cache
```

**What happens:**
- Creates empty MSAL cache object
- If `session["token_cache"]` exists, loads it
- Returns cache object for MSAL to use

#### 3. **Saving Token Cache** (`_save_cache()`)

```python
def _save_cache(cache):
    """Save token cache to session"""
    if cache.has_state_changed:
        # Serialize MSAL cache to string
        session["token_cache"] = cache.serialize()
```

**What happens:**
- Checks if cache was modified
- Serializes cache to JSON string
- Stores in session (which is saved to file)

#### 4. **Using Tokens Later** (`_get_token_from_cache()`)

```python
def _get_token_from_cache():
    """Get valid access token from cache or refresh if needed"""
    cache = _load_cache()  # Load from session
    accounts = auth_service.get_accounts(cache=cache)
    
    if accounts:
        # Try to get token silently (uses refresh token if needed)
        result = auth_service.acquire_token_silent(
            account=accounts[0],
            cache=cache
        )
        
        if result and "access_token" in result:
            _save_cache(cache)  # Save any updates (new refresh token)
            return result["access_token"]
    
    return None
```

**What happens:**
- Loads cache from session
- MSAL checks if token is still valid
- If expired, MSAL uses refresh token automatically
- Returns fresh access token
- Saves updated cache back to session

---

## 📦 What's Actually Stored in Session

### Session Data Structure

```python
session = {
    # Authentication state
    'authenticated': True,  # Boolean flag
    
    # User information
    'user': {
        'name': 'John Doe',
        'email': 'john.doe@company.com'
    },
    
    # MSAL Token Cache (THE IMPORTANT PART)
    'token_cache': '{"AccessToken": {...}, "RefreshToken": {...}, "IdToken": {...}}',
    # ^ This is a serialized JSON string containing:
    #   - access_token: For API calls (expires in ~1 hour)
    #   - refresh_token: To get new access tokens (expires in 90 days)
    #   - id_token: User identity information
    
    # OAuth flow state
    'state': 'uuid-for-csrf-protection',
    
    # Return destination after login
    'returnToSummary': {
        'type': 'teams',
        'id': '123'
    },
    
    # User email (for convenience)
    'email': 'john.doe@company.com'
}
```

### Token Cache Contents (Detailed)

The `token_cache` string deserializes to:

```json
{
  "AccessToken": {
    "credential_type": "AccessToken",
    "secret": "eyJ0eXAiOiJKV1QiLCJub25jZSI6...",  // Actual JWT token
    "home_account_id": "...",
    "environment": "login.microsoftonline.com",
    "client_id": "your-client-id",
    "target": "User.Read Calendars.Read Chat.ReadWrite ...",
    "cached_at": 1704816000,
    "expires_on": 1704819600,  // Expiration timestamp
    "extended_expires_on": 1704823200
  },
  "RefreshToken": {
    "credential_type": "RefreshToken",
    "secret": "0.AXsA7tK...",  // Refresh token (long-lived)
    "home_account_id": "...",
    "environment": "login.microsoftonline.com",
    "client_id": "your-client-id",
    "target": "User.Read Calendars.Read Chat.ReadWrite ..."
  },
  "IdToken": {
    "credential_type": "IdToken",
    "secret": "eyJ0eXAiOiJKV1QiLCJhbGciOiJ...",  // ID token (user info)
    "home_account_id": "...",
    "environment": "login.microsoftonline.com",
    "client_id": "your-client-id",
    "realm": "your-tenant-id"
  },
  "Account": {
    "home_account_id": "...",
    "environment": "login.microsoftonline.com",
    "realm": "your-tenant-id",
    "local_account_id": "...",
    "username": "john.doe@company.com",
    "authority_type": "MSSTS"
  }
}
```

---

## 🔄 Complete Token Lifecycle

### Diagram: OAuth Token Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER LOGS IN                                             │
├─────────────────────────────────────────────────────────────┤
│ User → Login → Microsoft → Auth Code → Your App            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. EXCHANGE CODE FOR TOKENS                                 │
├─────────────────────────────────────────────────────────────┤
│ auth_service.acquire_token_by_auth_code(code, cache)        │
│   ├─ MSAL calls Microsoft token endpoint                    │
│   ├─ Receives: access_token, refresh_token, id_token        │
│   └─ Writes to cache object                                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. SAVE TO SESSION                                          │
├─────────────────────────────────────────────────────────────┤
│ _save_cache(cache)                                          │
│   ├─ cache.serialize() → JSON string                        │
│   ├─ session["token_cache"] = JSON string                   │
│   └─ Flask-Session saves to file:                           │
│       flask_session/2029240f6d1128be89ddc32729463129        │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. USER MAKES REQUEST (10 minutes later)                    │
├─────────────────────────────────────────────────────────────┤
│ Browser sends: Cookie: session=2029240f...                  │
│   ├─ Flask reads: flask_session/2029240f...                 │
│   └─ Loads session data into memory                         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. GET TOKEN FROM CACHE                                     │
├─────────────────────────────────────────────────────────────┤
│ _get_token_from_cache()                                     │
│   ├─ cache = _load_cache()                                  │
│   │   └─ cache.deserialize(session["token_cache"])          │
│   ├─ auth_service.acquire_token_silent(account, cache)      │
│   │   ├─ MSAL checks: Is access_token still valid?          │
│   │   │   ├─ YES → Return existing token                    │
│   │   │   └─ NO → Use refresh_token to get new one          │
│   │   └─ Returns: {"access_token": "..."}                   │
│   └─ _save_cache(cache)  # Save any updates                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. USE TOKEN FOR API CALL                                   │
├─────────────────────────────────────────────────────────────┤
│ graph_service.send_chat_message(meeting_id, summary,        │
│                                   participants, access_token)│
│   └─ Headers: Authorization: Bearer <access_token>          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Considerations

### Why Filesystem Sessions Are Secure Enough for Development

1. **Data never in browser**
   - Only session ID in cookie
   - Actual tokens stored on server

2. **File permissions**
   - Files readable only by your user/app
   - Not accessible via web browser

3. **Signed cookies**
   - `app.secret_key` signs the session ID
   - Prevents tampering

4. **Automatic expiration**
   - Files cleaned up on app restart (with `start_fresh.sh`)
   - Can set expiration times

### Why You Need Different Storage for Production

**Problem with filesystem sessions in production:**

```
Load Balancer
      ↓
   ┌──┴──┐
   ↓     ↓
Server1  Server2
   │        │
   ├─ flask_session/  ├─ flask_session/
   │  └─ 2029240f     │  └─ <different files>
   │                  │
   
User's first request → Server1 → Creates session file
User's second request → Server2 → Can't find session! ❌
```

**Solution: Centralized session storage**

```
Load Balancer
      ↓
   ┌──┴──┐
   ↓     ↓
Server1  Server2
   ↓     ↓
   └──┬──┘
      ↓
   Redis Server (shared)
   └─ session:2029240f
```

---

## 🚀 Production Session Configuration

### Option 1: Redis (Recommended)

```python
# requirements.txt
redis==5.0.0
flask-session==0.5.0

# app.py
from redis import Redis
import os

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)
app.config['SESSION_KEY_PREFIX'] = 'transcript_app:'
```

**Advantages:**
- ✅ Fast (in-memory)
- ✅ Scalable (multiple servers)
- ✅ Built-in expiration
- ✅ Easy to deploy (Redis Cloud, Azure Cache, etc.)

### Option 2: Database

```python
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
```

**Advantages:**
- ✅ Persistent across Redis restarts
- ✅ Scalable
- ✅ Can query session data

### Option 3: Memcached

```python
app.config['SESSION_TYPE'] = 'memcached'
app.config['SESSION_MEMCACHED'] = memcache.Client(['127.0.0.1:11211'])
```

---

## 🧹 Session Cleanup

### Why `start_fresh.sh` Removes Session Files

```bash
#!/bin/bash
echo "🧹 Clearing old session data..."
rm -rf flask_session/
```

**Reasons:**
1. **Development testing** - Start with clean state
2. **Old sessions accumulate** - No auto-cleanup with filesystem
3. **Changed code** - Old session structure might be incompatible
4. **Debugging** - Remove corrupted sessions

### Production Cleanup

**Redis:** Automatic with TTL (Time To Live)
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

**Database:** Periodic cleanup job
```sql
DELETE FROM sessions WHERE expiry < NOW();
```

---

## 📊 Summary: Your Session Architecture

### Current Setup (Development)

```
Browser Cookie          Flask App              Filesystem
┌──────────┐           ┌──────────┐           ┌─────────────────┐
│ session= │ ←────────→│  Flask   │ ←────────→│ flask_session/  │
│ 2029240f │  HTTP     │  Session │  File I/O │ 2029240f...     │
└──────────┘           └────┬─────┘           └─────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │ session dict  │
                    │ {             │
                    │   'authenticated': True,
                    │   'user': {...},
                    │   'token_cache': '{...}'
                    │ }             │
                    └───────────────┘
```

### Production Setup (Recommended)

```
Browser Cookie          Flask App              Redis
┌──────────┐           ┌──────────┐           ┌─────────────────┐
│ session= │ ←────────→│  Flask   │ ←────────→│ Redis Server    │
│ 2029240f │  HTTP     │  Session │  Network  │ Key: transcript_│
└──────────┘           └────┬─────┘           │ app:2029240f    │
                            │                 │ Value: {...}    │
                            │                 │ TTL: 86400s     │
                            ↓                 └─────────────────┘
                    ┌───────────────┐                ↑
                    │ session dict  │                │
                    │ {             │                │
                    │   'authenticated': True,       │
                    │   'token_cache': '{...}'       │
                    │ }             │                │
                    └───────────────┘                │
                                                     │
                Multiple servers can access same Redis
```

---

## 💡 Key Takeaways

1. **Flask sessions store user data server-side**
   - Filesystem for development (physical files)
   - Redis/Database for production (shared storage)

2. **OAuth tokens saved in MSAL token cache**
   - Serialized to JSON string
   - Stored in session["token_cache"]
   - Automatically refreshed by MSAL

3. **Physical files are fine for development**
   - Simple setup
   - Easy debugging
   - No infrastructure needed

4. **Production needs centralized storage**
   - Multiple servers can share sessions
   - Faster than filesystem
   - Automatic cleanup

5. **Your code doesn't change**
   - Just update `SESSION_TYPE` configuration
   - Flask-Session handles the rest
   - MSAL token management stays the same

---

## 🔧 Configuration Summary

### Development (.env)
```bash
SESSION_TYPE=filesystem
SESSION_PERMANENT=false
```

### Production (.env)
```bash
SESSION_TYPE=redis
REDIS_URL=redis://your-redis-server:6379/0
SESSION_PERMANENT=false
SESSION_KEY_PREFIX=transcript_app:
SESSION_USE_SIGNER=true
SESSION_COOKIE_SECURE=true  # HTTPS only
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

Your current setup is perfect for development! 🎉
