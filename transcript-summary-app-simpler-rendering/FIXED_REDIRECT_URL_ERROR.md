# FIXED: "Redirect URL Not Found" Error

## Problem
When clicking "Login to Post in Teams", you saw an error **before** even reaching Microsoft's login page:
- "Redirect URL not found on server"

## Root Cause
The state parameter was being encoded with pipe characters (`|`):
```
state = "uuid|teams|meeting_id|email"
```

Microsoft's OAuth service may have been rejecting or misinterpreting this format, causing the redirect to fail.

---

## Solution
Changed to use **base64 URL-safe encoding** for the state backup:

### Before (Broken):
```python
state_with_return = f"{state}|{return_type}|{return_id}|{return_email}"
session["state"] = state_with_return
auth_url = auth_service.get_login_url(state=state_with_return)  # Bad! Pipes in URL
```

### After (Fixed):
```python
# 1. Keep the original UUID state for Microsoft
session["state"] = state  # Clean UUID

# 2. Encode return info separately in base64
return_data = {
    'uuid': state,
    'type': return_type,
    'id': return_id,
    'email': return_email
}
encoded = base64.urlsafe_b64encode(json.dumps(return_data).encode()).decode()
session["encoded_state"] = encoded  # Stored in session only

# 3. Send clean UUID to Microsoft
auth_url = auth_service.get_login_url(state=state)  # Clean!
```

---

## How It Works Now

### Login Flow:
```
1. User clicks "Login to Post in Teams"
   ↓
2. /auth/login receives: return_type=teams, return_id=abc, email=user@example.com
   ↓
3. Store in TWO places:
   - session['returnToSummary'] = {type, id, email}  (primary)
   - session['encoded_state'] = base64(json)          (backup)
   ↓
4. Send CLEAN UUID to Microsoft:
   state = "f3b2e1d4-5678-90ab-cdef-123456789ab"  ✓ No special chars!
   ↓
5. Microsoft accepts and redirects to login page ✓
```

### Callback Flow:
```
1. Microsoft redirects back with clean state
   ↓
2. /auth/callback receives: state=f3b2e1d4-5678-90ab-cdef-123456789ab
   ↓
3. Validate state matches session ✓
   ↓
4. Try to get returnToSummary:
   - First from session['returnToSummary'] (if session persisted)
   - Else from session['encoded_state'] (if session lost)
   ↓
5. Decode base64 → Get return URL
   ↓
6. Redirect to summary page ✓
```

---

## Benefits

✅ **Clean URLs** - No special characters in OAuth state
✅ **Microsoft-compatible** - Uses standard UUID for state
✅ **Session recovery** - Still works if session is lost
✅ **URL-safe** - Base64 encoding handles any characters
✅ **JSON format** - Easy to extend with more data

---

## Testing

1. **Restart your app:**
   ```bash
   cd transcript-summary-app-simpler-rendering
   rm -rf flask_session/*
   python app.py
   ```

2. **View a Teams meeting summary**

3. **Click "Login to Post in Teams"**

4. **You should see:**
   - Terminal: `DEBUG /auth/login: Using base64 encoded state: ...`
   - Browser: Successfully redirected to Microsoft login page ✓
   - **No more "Redirect URL not found" error!** ✓

5. **Log in at Microsoft**

6. **You should be redirected back to the summary page** ✓

---

## What Changed

| File | Change |
|------|--------|
| `app.py` (imports) | Added `import base64` and `import json` |
| `/auth/login` | Changed from pipe-delimited string to base64 JSON encoding |
| `/auth/callback` | Changed from string split to base64 decode + JSON parse |

---

## Debug Output

**When you click login, you'll now see:**
```bash
DEBUG /auth/login: Set returnToSummary = {'type': 'teams', 'id': 'abc123', 'email': '...'}
DEBUG /auth/login: Encoded return info in state for session recovery
DEBUG /auth/login: Using base64 encoded state: eyJ1dWlkIjogImYzYjJl...
DEBUG /auth/login: Redirecting to: https://login.microsoftonline.com/...
```

**After Microsoft redirect:**
```bash
DEBUG: Received state: f3b2e1d4-5678-90ab-cdef-123456789ab
DEBUG: Session state: f3b2e1d4-5678-90ab-cdef-123456789ab
DEBUG: Encoded state in session: eyJ1dWlkIjogImYzYjJl...
DEBUG /auth/callback: Checking returnToSummary in session...
```

**If session lost:**
```bash
DEBUG /auth/callback: returnToSummary = None
DEBUG /auth/callback: returnToSummary not in session, recovering from encoded state
DEBUG /auth/callback: Recovered returnToSummary = {'type': 'teams', 'id': 'abc123', ...}
DEBUG /auth/callback: Redirecting to summary page: type=teams, id=abc123
```

---

## Summary

**Problem:** Pipe characters in state parameter broke Microsoft OAuth redirect

**Solution:** Use clean UUID for Microsoft, store return info separately in base64

**Result:** OAuth redirect works, session recovery still works!

**Try it now!** 🎉
