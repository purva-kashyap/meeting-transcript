# OAuth Flow Diagrams

## Current Issue: "Unexpected token '<'" Error

### What Was Happening (Before Fix)
```
┌─────────────────────────────────────────────────────────────┐
│ Summary Page (Parent Window)                                │
│ - User clicks "Login to Post in Teams"                      │
│ - Opens popup window                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Login Popup Window (Separate Session Context)               │
│ - Mock login page loads                                      │
│ - User clicks "Accept & Sign In"                            │
│ - Session set: authenticated=true ✓                         │
│ - postMessage sent to parent                                │
│ - Window closes                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Summary Page Reloads (Parent Window)                        │
│ - Receives postMessage                                       │
│ - Calls window.location.reload()                            │
│ - Session: authenticated=false ❌                           │
│   (Session cookie from popup not shared!)                   │
│ - Still shows "Login to Post in Teams" button              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ User clicks "Send in Teams"
                       │
┌─────────────────────────────────────────────────────────────┐
│ POST /teams/send-summary                                     │
│ - _is_authenticated() returns False                         │
│ - Returns: jsonify({'error': 'Not authenticated'})          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ Fetch tries to parse as JSON
                       │
┌─────────────────────────────────────────────────────────────┐
│ Error: "Unexpected token '<', "<!DOCTYPE "... is not JSON"  │
│                                                              │
│ Why? The server redirected to login page (HTML)            │
│ instead of returning JSON error                             │
└─────────────────────────────────────────────────────────────┘
```

### Root Causes
1. **Popup has separate session cookie** - auth state not shared with parent
2. **Redirect instead of JSON** - `/teams/send-summary` returned HTML login page
3. **Fetch expected JSON** - Got `<!DOCTYPE html>` instead

---

## After Fix: Same-Window Redirect

### Fixed Flow (Current)
```
┌─────────────────────────────────────────────────────────────┐
│ Summary Page                                                 │
│ URL: /teams/meeting/123/summary?email=user@example.com      │
│ Session: authenticated=false                                 │
│ Shows: "🔐 Login to Post in Teams" button                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ User clicks "Login"
                       │
┌─────────────────────────────────────────────────────────────┐
│ loginToSend() JavaScript Function                           │
│ window.location.href = '/auth/login?return_type=teams       │
│                         &return_id=123'                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ Browser navigates (same window)
                       │
┌─────────────────────────────────────────────────────────────┐
│ /auth/login Route (Flask)                                   │
│ - Stores return info in session:                            │
│   session['returnToSummary'] = {                            │
│     'type': 'teams',                                         │
│     'id': '123'                                              │
│   }                                                          │
│ - Redirects to auth_service.get_login_url()                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
           ┌───────────┴────────────┐
           │                        │
     MOCK MODE              PRODUCTION MODE
           │                        │
           ↓                        ↓
┌──────────────────────┐ ┌─────────────────────────────────────┐
│ /auth/mock-login     │ │ Microsoft Login Page                │
│                      │ │ https://login.microsoft.com/...     │
│ [Mock Login UI]      │ │                                     │
│ - User clicks Accept │ │ - User enters credentials           │
│                      │ │ - User consents to permissions      │
└────────┬─────────────┘ └────────┬────────────────────────────┘
         │                        │
         ↓                        ↓
┌──────────────────────┐ ┌─────────────────────────────────────┐
│ /auth/mock-callback  │ │ /auth/callback                      │
│ - Sets session:      │ │ - Receives auth code                │
│   authenticated=true │ │ - Exchanges for access token        │
│   user info          │ │ - Saves token to session cache      │
│   access_token       │ │ - Gets user profile from MS Graph   │
│                      │ │ - Sets session: user info           │
└────────┬─────────────┘ └────────┬────────────────────────────┘
         │                        │
         └────────┬───────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│ Check session['returnToSummary']                            │
│ - Found: {'type': 'teams', 'id': '123'}                     │
│ - Build redirect URL:                                        │
│   /teams/meeting/123/summary?email=user@example.com         │
│ - return redirect(url)                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ Browser navigates (same window)
                       │
┌─────────────────────────────────────────────────────────────┐
│ Summary Page (Same Window, Same Session!)                   │
│ URL: /teams/meeting/123/summary?email=user@example.com      │
│ Session: authenticated=true ✓                               │
│         user={'name': 'Mock User', 'email': '...'}          │
│         access_token='...'                                   │
│ Template renders with: authenticated=True                   │
│ Shows: "📤 Send in Teams" button ✓                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓ User clicks "Send in Teams"
                       │
┌─────────────────────────────────────────────────────────────┐
│ sendToTeams() JavaScript Function                           │
│ fetch('/teams/send-summary', {                              │
│   method: 'POST',                                            │
│   body: JSON.stringify({...})                               │
│ })                                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ POST /teams/send-summary (Flask)                            │
│ - _is_authenticated() checks session                        │
│ - Returns: True ✓                                           │
│ - Gets access token from cache                              │
│ - Calls graph_service.send_chat_message()                   │
│ - Returns: jsonify({'success': True, 'message': '...'})     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ JavaScript .then(response => response.json())               │
│ - Receives valid JSON ✓                                     │
│ - Shows: "✅ Summary sent successfully to Teams!"           │
└─────────────────────────────────────────────────────────────┘
```

### Why This Works
1. ✅ **Same browser window** = Same session cookie throughout
2. ✅ **Session persists** across redirects
3. ✅ **Authenticated state** properly stored and retrieved
4. ✅ **JSON response** from `/teams/send-summary` (not HTML)

---

## Session Cookie Flow

### Visual Representation

```
Browser                          Flask Server
┌──────────┐                    ┌─────────────────┐
│          │                    │ Session Storage │
│  Window  │                    │ (filesystem)    │
│          │                    │                 │
│ Cookie:  │                    │ File: 2029240f  │
│ session= │◄──────────────────►│ Data:           │
│ 2029240f │  Same cookie ID    │ {               │
│          │  sent with every   │   authenticated │
│          │  request           │   user: {...}   │
│          │                    │   access_token  │
└──────────┘                    │ }               │
                                └─────────────────┘

Request 1: GET /teams/meeting/123/summary
├─ Cookie: session=2029240f
├─ Server reads: flask_session/2029240f
└─ authenticated=false → Shows "Login" button

Request 2: GET /auth/login?return_type=teams&return_id=123
├─ Cookie: session=2029240f (same!)
├─ Server writes: returnToSummary={'type': 'teams', 'id': '123'}
└─ Redirects to /auth/mock-login

Request 3: GET /auth/mock-login
├─ Cookie: session=2029240f (same!)
└─ Shows login form

Request 4: POST /auth/mock-callback
├─ Cookie: session=2029240f (same!)
├─ Server writes: authenticated=true, user={...}, access_token=...
└─ Returns: {redirect: '/teams/meeting/123/summary'}

Request 5: GET /teams/meeting/123/summary
├─ Cookie: session=2029240f (same!)
├─ Server reads: authenticated=true ✓
└─ Shows "Send in Teams" button ✓

Request 6: POST /teams/send-summary
├─ Cookie: session=2029240f (same!)
├─ Server reads: authenticated=true ✓
└─ Returns: {'success': true} (JSON) ✓
```

---

## Production OAuth Flow Comparison

### Mock vs Production (Side by Side)

```
┌──────────────────────────┬──────────────────────────────────┐
│ MOCK MODE                │ PRODUCTION MODE                  │
├──────────────────────────┼──────────────────────────────────┤
│ 1. Click "Login"         │ 1. Click "Login"                 │
│    ↓                     │    ↓                             │
│ 2. /auth/login           │ 2. /auth/login                   │
│    Store return info     │    Store return info             │
│    ↓                     │    ↓                             │
│ 3. Redirect to:          │ 3. Redirect to:                  │
│    /auth/mock-login      │    login.microsoft.com/...       │
│    ↓                     │    ↓                             │
│ 4. Show mock form        │ 4. Microsoft login page          │
│    Accept button         │    User enters creds             │
│    ↓                     │    User consents                 │
│ 5. POST /auth/mock-      │ 5. Microsoft redirects:          │
│    callback              │    /auth/callback?code=ABC...    │
│    ↓                     │    ↓                             │
│ 6. Set session:          │ 6. Exchange code for token       │
│    authenticated=true    │    Call MS Graph API             │
│    access_token=mock     │    Get real access token         │
│    ↓                     │    Set session with token cache  │
│ 7. Return redirect URL   │ 7. Redirect to summary           │
│    ↓                     │    ↓                             │
│ 8. Redirect to summary   │ 8. Summary page loads            │
│    ↓                     │    ↓                             │
│ 9. authenticated=true ✓  │ 9. authenticated=true ✓          │
├──────────────────────────┼──────────────────────────────────┤
│ REDIRECT URI:            │ REDIRECT URI:                    │
│ http://localhost:5001/   │ https://yourapp.com/             │
│ auth/callback            │ auth/callback                    │
│ (Not actually used)      │ (MUST match Azure config)        │
└──────────────────────────┴──────────────────────────────────┘
```

### Key Difference
- **Mock**: Internal redirect, no external OAuth server
- **Production**: External redirect to Microsoft, callback with auth code
- **Same Logic**: Both set session, both redirect back to summary, both work!

---

## Summary of Fix

### Problem
```
Popup Window → Separate Session → Auth Not Recognized → JSON Parse Error
```

### Solution  
```
Same Window → Single Session → Auth Persists → Success ✓
```

### Benefits
1. ✅ Simpler code (no popup handling)
2. ✅ Reliable session management
3. ✅ Works in mock and production
4. ✅ Standard OAuth pattern
5. ✅ No JSON parse errors
6. ✅ Better user experience
