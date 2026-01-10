# SESSION COOKIE FIX - Quick Start Guide

## Your Problem: State Mismatch Error After Login

You're seeing this because the **session cookie is lost** during the OAuth redirect from Microsoft back to your app.

---

## The Solution (Choose One)

### Option 1: Fix Session Cookies Properly (RECOMMENDED)

I've already added the session cookie configuration to your `app.py`:

```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allows OAuth redirects
app.config['SESSION_COOKIE_SECURE'] = False    # Required for localhost
app.config['SESSION_COOKIE_HTTPONLY'] = True   # Security
```

**Now do this:**

1. **Clear old sessions:**
   ```bash
   cd /Users/purvakashyap/Projects/meeting-transcript/transcript-summary-app-simpler-rendering
   rm -rf flask_session/*
   ```

2. **Restart your Flask app:**
   ```bash
   python app.py
   ```

3. **Use consistent URL:**
   - If your redirect URI is `http://localhost:5000/...` → Always use `localhost` in browser
   - If your redirect URI is `http://127.0.0.1:5000/...` → Always use `127.0.0.1` in browser
   - **Don't switch between them!**

4. **Test in Chrome** (best compatibility for cookies)

---

### Option 2: Bypass State Check Temporarily (DEBUG ONLY)

⚠️ **WARNING: This disables CSRF protection! Only use for debugging!**

If you just need to get it working quickly to test other features:

1. **Edit your `.env` file:**
   ```bash
   BYPASS_STATE_CHECK=true
   ```

2. **Restart your app:**
   ```bash
   python app.py
   ```

3. **You'll see warnings in the terminal** (this is intentional):
   ```
   ⚠️  WARNING: State check bypassed! This is a security risk
   ⚠️  Please fix your session cookie configuration
   ```

4. **After testing, turn it back off:**
   ```bash
   BYPASS_STATE_CHECK=false
   ```

---

## Checking If the Fix Worked

### Test 1: Check Session Cookie
1. Start your app: `python app.py`
2. Open browser → `http://localhost:5000` (or whatever your URL is)
3. Press F12 → Application → Cookies → `http://localhost:5000`
4. You should see a cookie named `flask_session` with:
   - **SameSite: Lax** ✓
   - **Secure: [empty]** (no checkmark for localhost) ✓
   - **HttpOnly: ✓** 

### Test 2: Check Debug Output
When you click "Post to Teams":

```bash
# Terminal should show:
DEBUG /auth/login: Generated state: abc-123-def-456
DEBUG /auth/login: Session ID: xyz789

# After Microsoft redirect:
DEBUG: Received state: abc-123-def-456
DEBUG: Session state: abc-123-def-456  # ← SHOULD MATCH!
```

✓ **If they match** → Session cookies are working!
❌ **If session state is None** → Session was lost

---

## Common Issues & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Session state is `None` | Cookie not preserved | Check SameSite=Lax is set |
| Session ID changes | New session created | Use consistent URL (localhost vs 127.0.0.1) |
| Cookie not visible in DevTools | Not created | Check Flask-Session is installed |
| Still state mismatch | Browser blocking cookies | Try Chrome, disable tracking protection |

---

## Quick Checklist

Before testing OAuth:

- [ ] Session cookie config is in `app.py` (already done ✓)
- [ ] Old sessions cleared: `rm -rf flask_session/*`
- [ ] App restarted
- [ ] Using consistent URL (localhost OR 127.0.0.1, not both)
- [ ] Testing in Chrome browser
- [ ] Checked DevTools for `flask_session` cookie with SameSite=Lax

---

## If You're Using the Bypass

Remember:
- ⚠️ **This is temporary** - don't deploy to production with this!
- ⚠️ **You're vulnerable to CSRF attacks** while bypass is enabled
- ⚠️ **Fix the real issue** (session cookies) as soon as possible

To fix properly:
1. Set `BYPASS_STATE_CHECK=false` in `.env`
2. Follow Option 1 above
3. Make sure your browser accepts cookies
4. Use consistent URLs

---

## Still Not Working?

Run the test script:
```bash
python test_session_cookies.py
```

This will check:
- If session cookie config is correct
- If cookies are being created
- If they have the right settings

Need more help? Share:
1. Terminal output from `/auth/login` and `/auth/callback`
2. Screenshot of DevTools → Cookies
3. Your browser name/version
