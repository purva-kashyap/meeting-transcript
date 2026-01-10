# SESSION RECOVERY FIX - Redirect After Login

## Problem
After successfully logging in to Microsoft, user was being redirected to home screen instead of back to the summary page.

**Root Cause:** The `returnToSummary` data stored in the session was lost during the OAuth redirect, causing the app to not know where to return the user.

---

## Solution Implemented

### **Dual Storage Strategy**

I've implemented a workaround that stores the return URL information in **TWO places**:

1. **Session** (primary method)
2. **State parameter** (backup for session loss)

This ensures the redirect works even if the session cookie is lost during OAuth.

---

## How It Works

### Before (Broken):

```
/auth/login?return_type=teams&return_id=abc123
    ↓
Store in session only:
session['returnToSummary'] = {'type': 'teams', 'id': 'abc123'}
    ↓
OAuth redirect to Microsoft
    ↓
Session cookie lost ❌
    ↓
/auth/callback - no returnToSummary in session
    ↓
Redirect to home (wrong!) ❌
```

### After (Fixed):

```
/auth/login?return_type=teams&return_id=abc123&email=user@example.com
    ↓
Store in TWO places:
1. session['returnToSummary'] = {'type': 'teams', 'id': 'abc123', 'email': '...'}
2. state = "uuid|teams|abc123|user@example.com" (encoded in state parameter)
    ↓
OAuth redirect to Microsoft with state parameter
    ↓
Microsoft redirects back with state
    ↓
/auth/callback?state=uuid|teams|abc123|user@example.com
    ↓
Try to get returnToSummary from session
If not found → Decode from state parameter ✓
    ↓
Redirect to /teams/meeting/abc123/summary?email=user@example.com ✓
```

---

## Code Changes

### 1. `/auth/login` - Dual Storage

```python
# Store in session (primary)
session['returnToSummary'] = {
    'type': return_type,
    'id': return_id,
    'email': return_email
}

# Also encode in state parameter (backup)
state_with_return = f"{state}|{return_type}|{return_id}|{return_email}"
session["state"] = state_with_return
```

### 2. `/auth/callback` - Recovery Logic

```python
# Try session first
return_info = session.get('returnToSummary')

# If not in session, recover from state parameter
if not return_info and len(received_state_parts) >= 3:
    return_info = {
        'type': received_state_parts[1],
        'id': received_state_parts[2],
        'email': received_state_parts[3] if len(received_state_parts) > 3 else ''
    }
    print("Recovered returnToSummary from state parameter!")

# Now redirect works!
```

### 3. `summary.html` - Pass Email Parameter

```javascript
function loginToSend() {
    const meetingId = '{{ meeting_id or "" }}';
    const meetingType = '{{ meetingType or "" }}';
    const email = '{{ email or "" }}';  // NEW: pass email
    const loginUrl = `/auth/login?return_type=${meetingType}&return_id=${meetingId}&email=${encodeURIComponent(email)}`;
    window.location.href = loginUrl;
}
```

---

## Testing

### 1. Restart App
```bash
cd transcript-summary-app-simpler-rendering
rm -rf flask_session/*
python app.py
```

### 2. Test the Flow

1. Go to home page → Enter email → Get Teams Meetings
2. Click on a meeting → View summary
3. Click "Login to Post in Teams"
4. Watch terminal output:

**You should see:**
```bash
DEBUG /auth/login: Set returnToSummary = {'type': 'teams', 'id': 'abc123', 'email': 'user@example.com'}
DEBUG /auth/login: Encoded return info in state for session recovery
```

5. Log in at Microsoft
6. After OAuth redirect, terminal should show:

**If session persisted (ideal):**
```bash
DEBUG /auth/callback: returnToSummary = {'type': 'teams', 'id': 'abc123', 'email': '...'}
DEBUG /auth/callback: Redirecting to summary page: type=teams, id=abc123
```

**If session was lost (backup kicks in):**
```bash
DEBUG /auth/callback: returnToSummary = None
DEBUG /auth/callback: returnToSummary not in session, recovering from state parameter
DEBUG /auth/callback: Recovered returnToSummary = {'type': 'teams', 'id': 'abc123', 'email': '...'}
DEBUG /auth/callback: Redirecting to summary page: type=teams, id=abc123
```

7. **Result:** You should be back on the summary page! ✓

---

## Benefits

✅ **Works even if session is lost** during OAuth
✅ **No need to fix session cookies** (though you still should)
✅ **Backwards compatible** (still uses session when available)
✅ **Maintains security** (state is still validated)

---

## Next Steps

This fix should work immediately. If you still see "redirecting to home":

1. **Check terminal output** - look for the debug messages
2. **Verify query parameters** - ensure `/auth/login?return_type=teams&return_id=...` is called
3. **Check for errors** - any exceptions would prevent the redirect

---

## Production Notes

This is a **robust workaround** but ideally you should still fix the root cause (session cookie persistence). Once session cookies work properly, the primary method (session storage) will be used and the state parameter backup won't be needed.

The state parameter backup is safe because:
- State is cryptographically random (CSRF protection maintained)
- Meeting ID is not sensitive (you need auth to access it anyway)
- Email is already public info in Teams

---

## Summary

**What was broken:** Session lost → no redirect info → home screen

**What's fixed now:** Redirect info encoded in state → survives session loss → correct redirect

**Test it now:** Restart app and try the login flow!
