# Debugging Redirect After Login

## Issue
After successfully logging in to Microsoft, user is redirected to home screen instead of back to the summary page.

## Root Cause Analysis

The redirect should work like this:

```
1. User views meeting summary
   ↓
2. User clicks "Login to Post in Teams"
   ↓
3. JavaScript calls: /auth/login?return_type=teams&return_id={meeting_id}
   ↓
4. Flask stores in session: session['returnToSummary'] = {'type': 'teams', 'id': meeting_id}
   ↓
5. User logs in at Microsoft
   ↓
6. Microsoft redirects to: /auth/callback?code=...&state=...
   ↓
7. Flask checks session for 'returnToSummary'
   ↓
8. If found: Redirect to /teams/meeting/{id}/summary
   If not found: Redirect to home ❌
```

## Possible Issues

### Issue 1: Session Lost During OAuth
If the session cookie is lost between steps 4 and 7, `returnToSummary` won't be in the session.

**Solution:** Ensure `SESSION_COOKIE_SAMESITE = 'Lax'` (already set ✓)

### Issue 2: State Mismatch Clears Session
If there's a state mismatch error, the user never reaches step 7.

**Check:** Look for "State mismatch error" in terminal

### Issue 3: Query Parameters Not Passed
The JavaScript might not be passing `return_type` and `return_id` correctly.

**Check:** Look for this in terminal:
```bash
DEBUG /auth/login: Set returnToSummary = {'type': 'teams', 'id': '...'}
```

If you see:
```bash
DEBUG /auth/login: No return_type/return_id provided (return_type=None, return_id=None)
```
Then the query parameters aren't reaching the server.

---

## Testing Steps

### 1. Start App with Fresh Session
```bash
cd transcript-summary-app-simpler-rendering
rm -rf flask_session/*
python app.py
```

### 2. View a Teams Meeting Summary
- Go to home page
- Enter email and date range
- Click "Get Teams Meetings"
- Click on a meeting
- You should see the summary page

### 3. Click "Login to Post in Teams"

Watch the terminal for these messages:

#### Expected Output (Correct):
```bash
DEBUG /auth/login: Generated state: abc-123-def...
DEBUG /auth/login: Session ID: 1234567890abcdef
DEBUG /auth/login: Set returnToSummary = {'type': 'teams', 'id': 'meeting-123'}
DEBUG /auth/login: Redirecting to: https://login.microsoftonline.com/...
```

#### Bad Output (Missing Parameters):
```bash
DEBUG /auth/login: Generated state: abc-123-def...
DEBUG /auth/login: Session ID: 1234567890abcdef
DEBUG /auth/login: No return_type/return_id provided (return_type=None, return_id=None)
DEBUG /auth/login: Redirecting to: https://login.microsoftonline.com/...
```

### 4. Log In at Microsoft
Complete the Microsoft login flow.

### 5. After Redirect, Check Terminal

#### Expected Output (Correct):
```bash
DEBUG: Received state: abc-123-def...
DEBUG: Session state: abc-123-def...
DEBUG: Session ID: 1234567890abcdef  (SAME AS BEFORE!)
DEBUG: Session contents: {'state': '...', 'returnToSummary': {'type': 'teams', 'id': '...'}, ...}
DEBUG /auth/callback: Checking returnToSummary in session...
DEBUG /auth/callback: returnToSummary = {'type': 'teams', 'id': 'meeting-123'}
DEBUG /auth/callback: Redirecting to summary page: type=teams, id=meeting-123
DEBUG /auth/callback: Teams redirect URL: /teams/meeting/meeting-123/summary?email=...
```

Then you should be redirected back to the summary page! ✓

#### Bad Output (Session Lost):
```bash
DEBUG: Received state: xyz-789-ghi...
DEBUG: Session state: abc-123-def...  (DIFFERENT!)
ERROR: State mismatch error. Received: xyz-789-ghi, Expected: abc-123-def
```

Or:

```bash
DEBUG: Received state: abc-123-def...
DEBUG: Session state: abc-123-def...  (MATCH!)
DEBUG: Session ID: 9876543210fedcba  (DIFFERENT - NEW SESSION!)
DEBUG: Session contents: {'state': '...'}  (NO returnToSummary!)
DEBUG /auth/callback: Checking returnToSummary in session...
DEBUG /auth/callback: returnToSummary = None
DEBUG /auth/callback: No returnToSummary found, redirecting to home
```

---

## Fixes Based on Test Results

### If "No return_type/return_id provided"

**Problem:** Query parameters not reaching Flask

**Check:**
1. Browser DevTools (F12) → Network tab
2. Click "Login to Post in Teams"
3. Look for request to `/auth/login`
4. Check the URL: Should be `/auth/login?return_type=teams&return_id=meeting-123`

**If URL is missing parameters:**
- Check `summary.html` line ~133: `loginToSend()` function
- Ensure `meeting_id` is set in template context

### If "State mismatch error"

**Problem:** Session cookie lost during OAuth

**Fix:** Set `BYPASS_STATE_CHECK=true` temporarily in `.env` to test

**In .env:**
```bash
BYPASS_STATE_CHECK=true  # TEMPORARY - FOR TESTING ONLY!
```

Then test again. If redirect works with bypass enabled, the issue is session cookies.

**Permanent fix:**
- Use consistent URLs (don't switch between localhost and 127.0.0.1)
- Check browser cookie settings
- Try Chrome (best compatibility)

### If "returnToSummary = None" (but states match)

**Problem:** Session cookie domain/path mismatch

**Check:**
1. Open F12 → Application → Cookies
2. Look at `flask_session` cookie
3. Check Domain and Path

**Should be:**
- Domain: `localhost` (or `127.0.0.1` if that's what you're using)
- Path: `/`
- SameSite: `Lax`

---

## Quick Fix for Testing

If you just want to test the send functionality without fixing the redirect:

**Option 1: Stay Logged In**
1. Log in once from home page
2. Then navigate to meetings/summary
3. You'll already be authenticated

**Option 2: Bypass State Check**
Set in `.env`:
```bash
BYPASS_STATE_CHECK=true
```

This is NOT secure for production but helps isolate the issue.

---

## Expected Terminal Output (Full Flow)

```bash
# User clicks "Login to Post in Teams"
DEBUG /auth/login: Generated state: f3b2e1d4-5678-90ab-cdef-1234567890ab
DEBUG /auth/login: Session ID: a1b2c3d4e5f6g7h8
DEBUG /auth/login: Session contents: {'state': 'f3b2e1d4...', 'returnToSummary': {'type': 'teams', 'id': 'abc123'}}
DEBUG /auth/login: Set returnToSummary = {'type': 'teams', 'id': 'abc123'}
DEBUG /auth/login: Redirecting to: https://login.microsoftonline.com/...

# User logs in at Microsoft, then redirected back
DEBUG: Received state: f3b2e1d4-5678-90ab-cdef-1234567890ab
DEBUG: Session state: f3b2e1d4-5678-90ab-cdef-1234567890ab
DEBUG: Session ID: a1b2c3d4e5f6g7h8
DEBUG: Session contents: {'state': 'f3b2e1d4...', 'returnToSummary': {'type': 'teams', 'id': 'abc123'}, 'token_cache': '...'}
DEBUG: BYPASS_STATE_CHECK: False
DEBUG /auth/callback: Checking returnToSummary in session...
DEBUG /auth/callback: returnToSummary = {'type': 'teams', 'id': 'abc123'}
DEBUG /auth/callback: Redirecting to summary page: type=teams, id=abc123
DEBUG /auth/callback: Teams redirect URL: /teams/meeting/abc123/summary?email=user@example.com

# Then summary page loads
DEBUG: Using cached summary for meeting abc123  (if cache exists)
```

**Final result:** User is back on summary page, authenticated, ready to send! ✓
