# Token Cache Flow - Visual Guide

## Current Flow (Filesystem Sessions)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LOGS IN                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Flask App calls: auth_service.acquire_token_by_auth_code()     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  MSAL ConfidentialClientApplication acquires tokens:            │
│  - Access Token  (valid for ~1 hour)                            │
│  - Refresh Token (valid for ~90 days)                           │
│  - ID Token      (user identity)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Tokens stored in: msal.SerializableTokenCache (in memory)      │
│                                                                  │
│  {                                                               │
│    "AccessToken": {                                              │
│      "secret": "eyJ0eXAiOiJKV1QiLCJub...",                      │
│      "expires_on": 1704567890,                                  │
│      "scope": "User.Read Calendars.Read..."                     │
│    },                                                            │
│    "RefreshToken": {                                             │
│      "secret": "0.AXEA1234...",                                  │
│      "expires_on": 1712343890                                   │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  _save_cache(cache) called                                      │
│  → cache.serialize()  # Converts to JSON string                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  session["token_cache"] = serialized_cache_json                 │
│                                                                  │
│  Flask session object (in memory):                              │
│  {                                                               │
│    "state": "abc-123-uuid",                                     │
│    "user": {"email": "user@example.com", "name": "User"},      │
│    "token_cache": "{\"AccessToken\": {...}}",  # JSON string    │
│    "summaries": {...}                                           │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Flask-Session writes session to FILESYSTEM                     │
│                                                                  │
│  File: ./flask_session/2029240f6d1128be89ddc32729463129        │
│  Contains: Pickled session data with token_cache inside         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Browser receives cookie: session=abc123...                     │
│  (Only session ID, NOT the actual tokens!)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Subsequent Requests (Token Retrieval)

```
┌─────────────────────────────────────────────────────────────────┐
│  User makes request (e.g., GET /teams/meetings)                 │
│  Browser sends: Cookie: session=abc123...                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Flask-Session loads session from FILESYSTEM                    │
│  File: ./flask_session/2029240f6d1128be89ddc32729463129        │
│  → Unpickles session data into session dict                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  _load_cache() called                                           │
│  → cache = msal.SerializableTokenCache()                        │
│  → cache.deserialize(session["token_cache"])                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Cache now has tokens in memory                                 │
│  {                                                               │
│    "AccessToken": {...},                                         │
│    "RefreshToken": {...}                                         │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  _get_token_from_cache() calls:                                 │
│  auth_service.acquire_token_silent(account, cache)              │
│                                                                  │
│  MSAL checks:                                                    │
│  1. Is access token in cache? ✅ Yes                            │
│  2. Is it expired? Check expires_on                             │
│     - If NOT expired: Return cached access token ✅             │
│     - If expired: Use refresh token to get new one ✅           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Access token returned to app                                   │
│  → Used in Graph API call: Authorization: Bearer eyJ0eXAi...    │
└─────────────────────────────────────────────────────────────────┘
```

---

## With Redis (Alternative)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LOGS IN                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
          (Token acquisition same as above)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  session["token_cache"] = serialized_cache_json                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Flask-Session writes session to REDIS (not filesystem!)        │
│                                                                  │
│  Redis Key: "session:abc123..."                                 │
│  Redis Value: {                                                  │
│    "state": "abc-123-uuid",                                     │
│    "user": {...},                                               │
│    "token_cache": "{\"AccessToken\": {...}}"                    │
│  }                                                               │
│  TTL: 86400 seconds (24 hours)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Browser receives cookie: session=abc123...                     │
└─────────────────────────────────────────────────────────────────┘

SUBSEQUENT REQUEST:
┌─────────────────────────────────────────────────────────────────┐
│  Browser sends: Cookie: session=abc123...                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Flask-Session loads from REDIS (FAST! in-memory)               │
│  → Redis GET "session:abc123..."                                │
│  → Returns session dict                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
          (Token retrieval same as filesystem flow)
```

---

## Storage Layers Explained

### Layer 1: MSAL Token Cache (Python Object)
```python
cache = msal.SerializableTokenCache()
# In-memory Python object with methods:
# - cache.add(...)      # Add tokens
# - cache.find(...)     # Find tokens
# - cache.serialize()   # Convert to JSON string
# - cache.deserialize() # Load from JSON string
```

### Layer 2: Serialization (JSON String)
```python
serialized = cache.serialize()
# Returns JSON string like:
# '{"AccessToken": {"client_id": "...", "secret": "eyJ0..."}}'
```

### Layer 3: Flask Session (Dict)
```python
session["token_cache"] = serialized
# Flask session is a dict-like object
# Stored per-user, identified by session cookie
```

### Layer 4: Storage Backend (Filesystem or Redis)
```python
# FILESYSTEM:
# File: ./flask_session/abc123...
# Contains: Pickled session dict

# REDIS:
# Key: "session:abc123..."
# Value: Serialized session dict
# TTL: Auto-expires after 24 hours
```

---

## Why This Multi-Layer Approach?

### Layer Separation Benefits

```
Application Code (app.py)
    ↕ (uses)
MSAL Cache (token management)
    ↕ (serializes to)
Flask Session (user session)
    ↕ (persists to)
Storage Backend (filesystem/Redis)
```

**Benefits:**
1. **Abstraction**: App code doesn't know about storage details
2. **Flexibility**: Easy to swap filesystem ↔ Redis
3. **Security**: Tokens never in browser, only session ID
4. **MSAL Features**: Automatic refresh, multi-scope support
5. **Session Features**: Secure cookies, HTTPOnly, SameSite

---

## Cache Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│                      TOKEN LIFECYCLE                          │
└──────────────────────────────────────────────────────────────┘

Time: 0:00        User logs in
                  ↓
                  Access Token acquired (expires in 1 hour)
                  Refresh Token acquired (expires in 90 days)
                  Both cached ✅

Time: 0:30        User makes API call
                  ↓
                  Access Token loaded from cache ✅
                  Not expired → Use it
                  API call succeeds ✅

Time: 1:15        User makes another API call
                  ↓
                  Access Token loaded from cache
                  EXPIRED! (1 hour passed) ⚠️
                  ↓
                  MSAL automatically uses Refresh Token
                  Gets NEW Access Token ✅
                  Updates cache with new token
                  API call succeeds ✅

Time: 24:00       Session expires
                  ↓
                  Filesystem: Session file deleted
                  Redis: Session key expired (TTL)
                  User must log in again

Time: 90 days     Refresh Token expires
                  ↓
                  Even if cached, can't refresh anymore
                  User must log in again
```

---

## Security Model

```
┌─────────────┐
│   Browser   │
│             │
│  Cookie:    │
│  session=   │
│  abc123...  │ ← Only session ID! No tokens!
└──────┬──────┘
       │
       │ HTTPS (in production)
       │
       ↓
┌─────────────────────────────────────────┐
│          Flask App Server                │
│                                          │
│  Session Storage:                        │
│  ┌────────────────────────────────────┐ │
│  │ Session ID: abc123...               │ │
│  │ Data:                               │ │
│  │   - user: {...}                     │ │
│  │   - token_cache: "{"AccessToken":  │ │
│  │       {"secret": "eyJ0..."}}"      │ │ ← Tokens stored SERVER-SIDE
│  └────────────────────────────────────┘ │
│                                          │
│  Never exposed to browser! ✅            │
└──────────────────────────────────────────┘
```

**Security Guarantees:**
- ✅ Tokens never sent to browser
- ✅ Tokens never in client-side JavaScript
- ✅ Session ID rotates on login
- ✅ HTTPOnly cookies prevent XSS
- ✅ SameSite=Lax prevents CSRF
- ✅ Secure flag in production (HTTPS only)

---

## Performance Comparison

### Filesystem (Current)

```
Request → Flask → Load session from DISK → Deserialize cache → Use token
         (1ms)        (10-50ms)              (1ms)           (0.1ms)
         
Total: ~12-52ms per request
```

**Bottleneck:** Disk I/O for session loading

### Redis (Alternative)

```
Request → Flask → Load session from REDIS → Deserialize cache → Use token
         (1ms)        (1-2ms)                (1ms)            (0.1ms)
         
Total: ~3-4ms per request
```

**Improvement:** 5-10x faster session access

---

## When to Use Each Approach

### Filesystem ✅ Use When:
```
✓ Development/Testing
✓ Single server deployment
✓ Low traffic (< 100 concurrent users)
✓ Simple setup (no Redis needed)
✓ Session persistence not critical
✓ OK with slower session access
```

### Redis ✅ Use When:
```
✓ Production deployment
✓ Multiple servers (load balanced)
✓ High traffic (100+ concurrent users)
✓ Need fast session access
✓ Want automatic cleanup (TTL)
✓ Sharing sessions across servers
```

---

## Code Comparison: Filesystem vs Redis

### Current (Filesystem)
```python
# app.py
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Session files in: ./flask_session/
# Each user: ./flask_session/abc123...
# Cleanup: Manual (delete old files)
```

### With Redis
```python
# app.py
import redis

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)

# Sessions in: Redis database
# Each user: Key "session:abc123..." with TTL
# Cleanup: Automatic (TTL expiration)
```

**Cache code stays IDENTICAL!** 🎉

```python
# These functions don't change at all:
def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
```

---

## Summary

**What is the cache?**
- MSAL SerializableTokenCache (Python object)
- Serialized to JSON string
- Stored in Flask session["token_cache"]
- Session persisted to filesystem (current) or Redis (optional)

**Can we use in-memory cache?**
- ✅ YES - Switch Flask session to Redis
- ✅ Minimal code changes (just config)
- ✅ Cache code stays identical
- ✅ Much faster than filesystem
- ✅ Recommended for production

**Current approach:**
- ✅ Works perfectly for development
- ✅ Production-ready for single server
- ✅ Simple, no additional dependencies

**Redis approach:**
- ✅ Better for production
- ✅ Faster (5-10x)
- ✅ Scales to multiple servers
- ✅ Automatic cleanup
- ⚠️ Requires Redis service

**Recommendation:**
- Keep filesystem for now ✅
- Switch to Redis when scaling up 🚀
