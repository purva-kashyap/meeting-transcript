# Troubleshooting: State Mismatch Error

## ❌ Error Message
```
State mismatch error
```

This error occurs during the OAuth callback when the `state` parameter from Microsoft doesn't match what's stored in your session.

---

## 🔍 Root Causes & Solutions

### 1. **URL Inconsistency (Most Common)**

**Problem:** You started login at `http://localhost:5001` but Microsoft redirected to `http://127.0.0.1:5001` (or vice versa).

**Why it happens:**
- Browsers treat `localhost` and `127.0.0.1` as different domains for cookies
- Session cookie set on `localhost` won't be sent when accessing `127.0.0.1`
- Without the session cookie, Flask can't retrieve the stored `state`

**Solution:**

1. **Choose ONE and stick with it:**
   - Option A: Always use `localhost`
   - Option B: Always use `127.0.0.1`

2. **Update Azure Portal redirect URI to match:**

   **If using `localhost`:**
   ```
   Azure Portal → Your App → Authentication → Web platform
   Redirect URI: http://localhost:5001/auth/callback
   ```
   
   **If using `127.0.0.1`:**
   ```
   Azure Portal → Your App → Authentication → Web platform
   Redirect URI: http://127.0.0.1:5001/auth/callback
   ```

3. **Update .env to match:**
   ```bash
   # Match exactly what's in Azure
   MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback
   ```

4. **Access app consistently:**
   ```bash
   # If you chose localhost, always use:
   http://localhost:5001
   
   # If you chose 127.0.0.1, always use:
   http://127.0.0.1:5001
   ```

---

### 2. **Session Storage Issue**

**Problem:** Session file was deleted or corrupted between login initiation and callback.

**Check:**
```bash
# List session files
ls -la flask_session/

# If empty or missing, sessions aren't being saved
```

**Solution:**

1. **Ensure session directory exists:**
   ```bash
   mkdir -p flask_session
   chmod 755 flask_session
   ```

2. **Check Flask-Session configuration:**
   ```python
   # In app.py - verify these are set:
   app.config['SESSION_TYPE'] = 'filesystem'
   Session(app)
   ```

3. **Restart app:**
   ```bash
   ./start_fresh.sh
   ```

---

### 3. **Browser Cookie Issues**

**Problem:** Browser not accepting/sending session cookies.

**Check in Browser DevTools:**
1. Open DevTools (F12)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click **Cookies** → `http://localhost:5001`
4. Look for `session` cookie

**Solution:**

**If no session cookie:**
- Check if browser is in Private/Incognito mode
- Disable ad blockers/privacy extensions temporarily
- Try a different browser

**If cookie exists but not sent:**
- Cookie domain might be wrong
- Clear all cookies for localhost
- Restart browser

---

### 4. **Multiple Tabs/Windows**

**Problem:** Opening login in new tab creates a new session.

**Current Code:** You're using same-window redirect, so this shouldn't happen. But if you manually opened a new tab:

**Solution:**
- Don't manually copy the Microsoft login URL to a new tab
- Let the app handle the redirect
- If you need to restart, go back to your app's home page and start fresh

---

### 5. **Session Timeout**

**Problem:** Too much time passed between login initiation and completing Microsoft login.

**Check:**
```python
# Check if session has expiration set
app.config['PERMANENT_SESSION_LIFETIME']
```

**Solution:**

1. **For development, increase timeout:**
   ```python
   # Add to app.py after Session(app)
   from datetime import timedelta
   app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
   ```

2. **Complete login quickly:**
   - Don't leave login page idle
   - Complete within a few minutes

---

### 6. **Redirect URI Mismatch**

**Problem:** The redirect URI in your code doesn't match what Microsoft expects.

**Check:**

1. **What Microsoft will use:**
   - The `redirect_uri` parameter sent in the authorization request
   - This comes from `auth_service.redirect_uri`

2. **What your callback expects:**
   - Your Flask route: `/auth/callback`
   - Full URL: `http://localhost:5001/auth/callback`

**Solution:**

Ensure they match:

```bash
# .env file
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback

# Azure Portal
Redirect URI: http://localhost:5001/auth/callback
```

---

## 🧪 Testing & Debugging

### Step 1: Check Debug Logs

I've added debug logging. When you test, check the console output:

**At `/auth/login`:**
```
DEBUG /auth/login: Generated state: abc-123-xyz
DEBUG /auth/login: Session ID: 2029240f6d1128be89ddc32729463129
DEBUG /auth/login: Session contents: {'state': 'abc-123-xyz', ...}
DEBUG /auth/login: Redirecting to: https://login.microsoftonline.com/...
```

**At `/auth/callback`:**
```
DEBUG: Received state: abc-123-xyz
DEBUG: Session state: abc-123-xyz  ← Should match!
DEBUG: Session ID: 2029240f6d1128be89ddc32729463129  ← Should match login!
DEBUG: Session contents: {'state': 'abc-123-xyz', ...}
```

**If they don't match:**
- Session was lost
- Different session cookie

### Step 2: Verify URL Consistency

```bash
# Check what URL you're using
# In browser address bar, should be ONE of:
http://localhost:5001/auth/login
# OR
http://127.0.0.1:5001/auth/login

# After Microsoft redirect, should be SAME:
http://localhost:5001/auth/callback?code=...&state=...
# OR
http://127.0.0.1:5001/auth/callback?code=...&state=...
```

### Step 3: Check Session Files

```bash
# Before clicking login
ls -la flask_session/
# Should show at least one file

# Check what's in a session file
cat flask_session/<session-id>
# Should see 'state' key
```

### Step 4: Test End-to-End

```bash
# 1. Clear everything
./start_fresh.sh

# 2. Check app is running
curl http://localhost:5001/debug/msal-config

# 3. Open browser to (choose ONE):
http://localhost:5001

# 4. Start login flow
# Click "Login to Post in Teams"

# 5. Watch console logs
# Should see DEBUG /auth/login messages

# 6. Complete Microsoft login

# 7. Watch console logs again
# Should see DEBUG /auth/callback messages

# 8. If state mismatch:
# - Compare session IDs in logs
# - Check URL in browser address bar
```

---

## 🔧 Quick Fixes

### Fix 1: Use Localhost Consistently

```bash
# 1. Update .env
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback

# 2. Update Azure Portal
Redirect URI: http://localhost:5001/auth/callback

# 3. Restart app
./start_fresh.sh

# 4. ALWAYS access via:
http://localhost:5001
```

### Fix 2: Clear Everything and Retry

```bash
# 1. Clear sessions
rm -rf flask_session/

# 2. Clear browser cookies
# DevTools → Application → Cookies → localhost → Delete all

# 3. Restart app
./start_fresh.sh

# 4. Try again
```

### Fix 3: Increase Session Lifetime

Add to `app.py` after `Session(app)`:

```python
from datetime import timedelta

# Configure server-side session
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
app.config['SESSION_PERMANENT'] = os.getenv('SESSION_PERMANENT', 'false').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # ← Add this
Session(app)
```

---

## 📋 Verification Checklist

Before testing again:

- [ ] Using consistent URL (`localhost` OR `127.0.0.1`, not both)
- [ ] Azure redirect URI matches .env exactly
- [ ] .env `MICROSOFT_REDIRECT_URI` matches Azure
- [ ] `flask_session/` directory exists
- [ ] App restarted with `./start_fresh.sh`
- [ ] Browser cookies enabled
- [ ] Not in Private/Incognito mode
- [ ] Ad blockers disabled (for testing)

---

## 🎯 Expected Flow

**Correct flow (no state mismatch):**

```
1. User visits: http://localhost:5001
   ↓
2. Clicks "Login to Post in Teams"
   ↓
3. App generates state: "abc-123"
   ↓
4. App saves state to session file: flask_session/xyz
   ↓
5. Browser gets session cookie: session=xyz
   ↓
6. App redirects to Microsoft with state=abc-123
   ↓
7. User completes Microsoft login
   ↓
8. Microsoft redirects to: http://localhost:5001/auth/callback?code=...&state=abc-123
   ↓
9. Browser sends request WITH session cookie: session=xyz
   ↓
10. App reads session file: flask_session/xyz
    ↓
11. App finds state: "abc-123"
    ↓
12. App compares: received "abc-123" == stored "abc-123" ✅
    ↓
13. Success! Proceed with token exchange
```

**Where it breaks (state mismatch):**

```
...
8. Microsoft redirects to: http://127.0.0.1:5001/auth/callback  ← Different domain!
   ↓
9. Browser sends request WITHOUT session cookie (wrong domain)
   ↓
10. App can't find session (no cookie)
    ↓
11. session.get("state") returns None
    ↓
12. App compares: received "abc-123" != stored None ❌
    ↓
13. ERROR: State mismatch!
```

---

## 🆘 If Still Having Issues

Run the diagnostic script:

```bash
./diagnose_azure_config.sh
```

Check these debug endpoints:

```bash
# Check session
curl http://localhost:5001/debug/session

# Check MSAL config
curl http://localhost:5001/debug/msal-config
```

Then share the console logs from both `/auth/login` and `/auth/callback`.

---

## 📚 Related Documentation

- `SESSION_EXPLAINED.md` - How Flask sessions work
- `REDIRECT_URI_GUIDE.md` - Redirect URI configuration
- `TROUBLESHOOT_PUBLIC_CLIENT_ERROR.md` - Azure app configuration
