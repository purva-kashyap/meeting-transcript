# Token Cache in Delegated Flow - Explained

## Current Implementation

### What Cache Are We Using?

**MSAL SerializableTokenCache** stored in **Flask server-side sessions** (filesystem).

### How It Works

```python
# 1. Load cache from session (deserialized)
def _load_cache():
    cache = msal.SerializableTokenCache()  # Create empty cache
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])  # Load from session
    return cache

# 2. Save cache to session (serialized)
def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()  # Save to session
```

### Storage Flow

```
User logs in
    ↓
MSAL acquires tokens (access + refresh)
    ↓
Tokens stored in SerializableTokenCache
    ↓
Cache serialized to JSON string
    ↓
Stored in Flask session["token_cache"]
    ↓
Flask session stored in filesystem (/flask_session/...)
```

### What's in the Cache?

```json
{
  "AccessToken": {
    "client_id": "your-client-id",
    "scope": "User.Read Calendars.Read ...",
    "token_type": "Bearer",
    "expires_in": 3599,
    "ext_expires_in": 3599,
    "access_token": "eyJ0eXAi...",  // JWT token
    "refresh_token": "0.AXEA...",    // Refresh token
    "id_token": "eyJ0eXAi...",
    // ... more metadata
  },
  "Account": {
    "username": "user@example.com",
    "environment": "login.microsoftonline.com",
    // ... user details
  }
}
```

---

## Why Not In-Memory Cache?

### Current Setup: Filesystem Session + Serialized Cache

**Pros:**
- ✅ **Persistent across requests** - User stays logged in
- ✅ **Survives app restarts** (session files remain)
- ✅ **Works with single server** (current setup)
- ✅ **No additional dependencies**
- ✅ **Simple to implement**

**Cons:**
- ⚠️ **Doesn't scale** to multiple servers (each has own filesystem)
- ⚠️ **Disk I/O overhead** (slower than memory)
- ⚠️ **Manual cleanup required** (old session files accumulate)

---

## In-Memory Cache Options

### Option 1: Simple In-Memory (Not Recommended)

```python
# Store cache directly in Python dict
token_cache = {}  # Global variable

def _load_cache(user_id):
    cache = msal.SerializableTokenCache()
    if user_id in token_cache:
        cache.deserialize(token_cache[user_id])
    return cache

def _save_cache(user_id, cache):
    if cache.has_state_changed:
        token_cache[user_id] = cache.serialize()
```

**Problems:**
- ❌ **Lost on app restart** - Users must re-login
- ❌ **Not shared across workers** - Each Gunicorn worker has separate memory
- ❌ **Memory leaks** - No automatic cleanup
- ❌ **Session still on filesystem** - Only cache moves to memory

**Verdict:** ❌ Don't use this approach

---

### Option 2: Redis-Backed Cache (Recommended for Production)

```python
import redis
import msal

# Initialize Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def _load_cache(user_id):
    cache = msal.SerializableTokenCache()
    cached_data = redis_client.get(f"token_cache:{user_id}")
    if cached_data:
        cache.deserialize(cached_data.decode('utf-8'))
    return cache

def _save_cache(user_id, cache):
    if cache.has_state_changed:
        # Store with 24-hour expiration
        redis_client.setex(
            f"token_cache:{user_id}",
            86400,  # 24 hours
            cache.serialize()
        )
```

**Pros:**
- ✅ **Fast** - In-memory performance
- ✅ **Persistent** - Survives app restarts (Redis has persistence)
- ✅ **Scalable** - Multiple servers share same Redis
- ✅ **Automatic expiration** - Built-in TTL cleanup
- ✅ **Production-ready** - Battle-tested solution

**Cons:**
- ⚠️ **Additional service** - Need to run Redis
- ⚠️ **Complexity** - More moving parts
- ⚠️ **Cost** - Redis hosting (if cloud)

**Verdict:** ✅ **Best for production with multiple servers**

---

### Option 3: Redis-Backed Sessions + Cache

```python
from flask import Flask
from flask_session import Session
import redis

app = Flask(__name__)

# Use Redis for Flask sessions
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')

Session(app)

# Cache is still serialized to session (now in Redis)
def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
```

**Pros:**
- ✅ **Minimal code changes** - Same cache logic
- ✅ **Fast** - Session in Redis (memory)
- ✅ **Scalable** - Multiple servers share Redis
- ✅ **Persistent** - Redis persistence
- ✅ **Automatic cleanup** - Session expiration

**Cons:**
- ⚠️ **Need Redis** - Additional dependency

**Verdict:** ✅ **Best balance of simplicity and scalability**

---

## Comparison Table

| Approach | Speed | Persistent | Multi-Server | Code Changes | Complexity |
|----------|-------|-----------|--------------|--------------|------------|
| **Filesystem (current)** | 🟡 Medium | ✅ Yes | ❌ No | None | 🟢 Low |
| **Python dict (in-memory)** | 🟢 Fast | ❌ No | ❌ No | Small | 🟢 Low |
| **Redis cache only** | 🟢 Fast | ✅ Yes | ✅ Yes | Medium | 🟡 Medium |
| **Redis sessions + cache** | 🟢 Fast | ✅ Yes | ✅ Yes | Small | 🟡 Medium |

---

## Should You Switch to In-Memory Cache?

### Stick with Current (Filesystem) If:
- ✅ Single server deployment (localhost, single VM)
- ✅ Low traffic (< 100 users)
- ✅ Prototyping / Development
- ✅ Simple deployment requirements

### Switch to Redis If:
- ✅ Multiple servers (load balanced)
- ✅ High traffic (100+ concurrent users)
- ✅ Production deployment
- ✅ Need fast session access
- ✅ Want automatic cleanup

---

## Implementation: Redis-Backed Sessions

If you want to switch to Redis (recommended for production):

### 1. Install Dependencies

```bash
pip install redis flask-session
```

### 2. Update requirements.txt

```txt
Flask==3.0.0
flask-session==0.5.0
redis==5.0.1
msal==1.24.0
requests==2.31.0
python-dotenv==1.0.0
```

### 3. Update app.py

```python
from flask import Flask, session
from flask_session import Session
import redis
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Redis configuration
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Configure Redis-backed sessions
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(redis_url)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

Session(app)

# Token cache functions stay the SAME
def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
```

### 4. Update .env

```bash
# Add Redis configuration
REDIS_URL=redis://localhost:6379
```

### 5. Start Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Linux (apt):**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

### 6. Test

```bash
python app.py
# Sessions now stored in Redis!
```

---

## How MSAL Cache Works Internally

### Token Types Stored

1. **Access Token**
   - Short-lived (1 hour typically)
   - Used for API calls
   - Cached with scope and expiration

2. **Refresh Token**
   - Long-lived (90 days typically)
   - Used to get new access tokens
   - Securely stored in cache

3. **ID Token**
   - Contains user identity claims
   - Used for user profile

### Cache Key Structure

```python
# MSAL internally creates keys like:
{
  "AccessToken.{client_id}.{user_id}.{scope_hash}": {...},
  "RefreshToken.{client_id}.{user_id}": {...},
  "IdToken.{client_id}.{user_id}": {...},
  "Account.{environment}.{user_id}": {...}
}
```

### Automatic Token Refresh

```python
# When you call acquire_token_silent():
result = auth_service.acquire_token_silent(account=account, cache=cache)

# MSAL automatically:
# 1. Checks if access token exists in cache
# 2. Checks if access token is expired
# 3. If expired, uses refresh token to get new access token
# 4. Updates cache with new tokens
# 5. Returns new access token
```

---

## Security Considerations

### Current Setup (Filesystem)
- ✅ Tokens stored server-side (not in browser cookies)
- ✅ Session ID in cookie (HTTPOnly, SameSite)
- ✅ Actual tokens on server filesystem
- ⚠️ File permissions must be correct (chmod 600)

### Redis Setup
- ✅ Tokens stored in Redis (in-memory)
- ✅ Session ID in cookie
- ✅ Redis should be password-protected
- ⚠️ Enable Redis AUTH: `redis-server --requirepass yourpassword`
- ⚠️ Use TLS for Redis connections in production

### Never Do This ❌
```python
# DON'T store tokens in client-side cookies
response.set_cookie('access_token', token)  # NEVER!

# DON'T store tokens in localStorage
# <script>localStorage.setItem('token', ...)</script>  # NEVER!
```

---

## Monitoring Cache Performance

### Add Logging

```python
import time

def _load_cache():
    start = time.time()
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    app.logger.info(f"Cache load took {(time.time() - start)*1000:.2f}ms")
    return cache
```

### Check Cache Size

```python
def _save_cache(cache):
    if cache.has_state_changed:
        serialized = cache.serialize()
        app.logger.info(f"Cache size: {len(serialized)} bytes")
        session["token_cache"] = serialized
```

---

## Recommendation

### For Your Current Setup (Development/Testing)
**Keep filesystem-based sessions** ✅
- Simple, works out of the box
- Good for single server
- No additional dependencies

### For Production Deployment
**Switch to Redis-backed sessions** ✅
- Fast, scalable, persistent
- Minimal code changes (just configuration)
- Industry standard

### Implementation Priority
1. **Now**: Keep filesystem (works perfectly)
2. **Before multi-server deployment**: Switch to Redis
3. **Monitor**: Add cache performance logging

---

## Quick Comparison: Current vs Redis

### Current (Filesystem)
```python
# app.py
app.config['SESSION_TYPE'] = 'filesystem'
# Session stored in: ./flask_session/abc123...
# Cache stored in: session["token_cache"] (in file)
```

### With Redis
```python
# app.py
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
# Session stored in: Redis key "session:abc123..."
# Cache stored in: session["token_cache"] (in Redis)
```

**Cache logic stays identical** - just storage backend changes!

---

## Summary

**What cache are we using?**
- MSAL SerializableTokenCache
- Serialized to JSON string
- Stored in Flask session
- Session stored on filesystem (current)

**Can we use in-memory cache?**
- ✅ Yes - Use Redis for sessions
- ✅ Minimal code changes
- ✅ Recommended for production
- ❌ Don't use Python dict (loses data on restart)

**Should you change now?**
- ❌ No - Current setup works perfectly for development
- ✅ Yes - When deploying to production with multiple servers
- ✅ Yes - When you need better performance
- ✅ Yes - When you want automatic cleanup

The current implementation is **production-ready** as-is for single-server deployments! 🚀
