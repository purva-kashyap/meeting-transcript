# Redirect URI Configuration Guide

## Your Azure Portal Setup

You have configured the redirect URI in Azure Portal as:
```
http://localhost:5001/redirect
```

## Changes Made to Support This

I've updated the code to match your Azure configuration. Here's what changed:

### 1. Updated `.env.example`

**Before:**
```bash
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback
```

**After:**
```bash
MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect
```

### 2. Updated `services/auth_service.py`

**Before:**
```python
self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:5001/auth/callback')
```

**After:**
```python
self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:5001/redirect')
```

### 3. Updated `app.py` Route

**Before:**
```python
@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Microsoft"""
    # ... code ...
```

**After:**
```python
@app.route('/redirect')
def auth_redirect():
    """Handle OAuth redirect from Microsoft"""
    # ... code ...
```

---

## What You Need to Do

### Update Your `.env` File

When you create your `.env` file from `.env.example`, make sure it has:

```bash
# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID=<your-client-id>
MICROSOFT_CLIENT_SECRET=<your-client-secret>
MICROSOFT_TENANT_ID=<your-tenant-id>
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/<your-tenant-id>
MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect  # ← Must match Azure!
```

**Critical**: The `MICROSOFT_REDIRECT_URI` in `.env` must **EXACTLY** match what's in Azure Portal!

---

## OAuth Flow with Your Configuration

```
User clicks "Show Teams Meetings"
    ↓
App redirects to Microsoft:
https://login.microsoftonline.com/.../oauth2/v2.0/authorize
  ?client_id=your-client-id
  &response_type=code
  &redirect_uri=http://localhost:5001/redirect  ← Your redirect URI
  &scope=User.Read+Calendars.Read...
  &state=abc-123-uuid
    ↓
User logs in and consents
    ↓
Microsoft redirects back to:
http://localhost:5001/redirect  ← Your Flask route
  ?code=abc123...
  &state=abc-123-uuid
    ↓
Flask route `/redirect` handles the callback
    ↓
Code exchanges authorization code for access token
    ↓
User is authenticated!
```

---

## Common Redirect URI Issues

### ❌ Error: "Redirect URI mismatch"

**Cause:**
The redirect URI in your request doesn't match what's registered in Azure Portal.

**Check these:**
1. **Azure Portal** → App registrations → Your app → Authentication
   - Should show: `http://localhost:5001/redirect`

2. **Your `.env` file**:
   ```bash
   MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect
   ```

3. **Must match EXACTLY:**
   - Protocol: `http://` (not `https://` for localhost)
   - Host: `localhost` (not `127.0.0.1`)
   - Port: `5001`
   - Path: `/redirect` (not `/auth/callback`)
   - No trailing slash!

### ✅ Correct Configurations

All three must match:

| Location | Value |
|----------|-------|
| **Azure Portal** | `http://localhost:5001/redirect` |
| **`.env` file** | `MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect` |
| **Flask route** | `@app.route('/redirect')` |

---

## Testing the Configuration

### 1. Verify Environment Variable

```bash
cd transcript-summary-delegated
cat .env | grep REDIRECT_URI
# Should show: MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect
```

### 2. Start the App

```bash
python app.py
# Should start on port 5001
```

### 3. Test Authentication

1. Visit: `http://localhost:5001`
2. Click "Show Teams Meetings"
3. You'll be redirected to Microsoft login
4. **Check the URL** - should include: `redirect_uri=http://localhost:5001/redirect`
5. After login, you should be redirected to: `http://localhost:5001/redirect?code=...&state=...`
6. If successful: You'll see the meetings page
7. If error: Check browser address bar for error message

### 4. Check Logs

Look for this in terminal:
```
INFO - OAuth callback - Received state: abc123, Session state: abc123
INFO - Successfully acquired access token
INFO - User authenticated: your.email@company.com
```

---

## Alternative: Change Azure to Match Original Code

If you prefer to keep the code as `/auth/callback`, you can change Azure Portal instead:

### Steps to Update Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Select your app
4. Click **Authentication** in left menu
5. Under **Web** → **Redirect URIs**:
   - Remove: `http://localhost:5001/redirect`
   - Add: `http://localhost:5001/auth/callback`
6. Click **Save**

Then update your `.env`:
```bash
MICROSOFT_REDIRECT_URI=http://localhost:5001/auth/callback
```

And revert the code changes (I can help with this if needed).

---

## Production Redirect URI

When deploying to production, you'll need to add the production redirect URI:

### In Azure Portal

Add **both** redirect URIs:
```
http://localhost:5001/redirect          (for local development)
https://your-domain.com/redirect        (for production)
```

### In Your `.env` (Development)
```bash
MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect
```

### In Production Environment Variables
```bash
MICROSOFT_REDIRECT_URI=https://your-domain.com/redirect
```

**Important:**
- Production **must** use `https://` (not `http://`)
- Azure allows multiple redirect URIs registered
- App uses the one from `MICROSOFT_REDIRECT_URI` environment variable

---

## Debugging Redirect URI Issues

### Enable Debug Logging

Add this to your `.env`:
```bash
FLASK_DEBUG=True
```

Then check logs when authenticating.

### Check Azure App Registration

```bash
# In Azure Portal, verify:
1. App registrations → Your app → Authentication
2. Platform: Web
3. Redirect URIs: http://localhost:5001/redirect ✓
4. No trailing slash!
```

### Test with Microsoft Graph Explorer

Visit: https://developer.microsoft.com/graph/graph-explorer

Try the same scopes to verify your app registration works.

### Common Mistakes

| Issue | Wrong | Correct |
|-------|-------|---------|
| **Trailing slash** | `http://localhost:5001/redirect/` | `http://localhost:5001/redirect` |
| **Wrong protocol** | `https://localhost:5001/redirect` | `http://localhost:5001/redirect` |
| **Wrong host** | `http://127.0.0.1:5001/redirect` | `http://localhost:5001/redirect` |
| **Wrong port** | `http://localhost:5000/redirect` | `http://localhost:5001/redirect` |
| **Case sensitive** | `http://localhost:5001/Redirect` | `http://localhost:5001/redirect` |

---

## Summary of Changes

✅ **Files Updated:**
1. `.env.example` - Changed default redirect URI
2. `services/auth_service.py` - Changed default redirect URI
3. `app.py` - Changed route from `/auth/callback` to `/redirect`

✅ **What You Need to Do:**
1. Create `.env` file with correct redirect URI
2. Verify Azure Portal has `http://localhost:5001/redirect`
3. Test authentication flow

✅ **Code is Ready:**
The app now expects redirect at `/redirect` to match your Azure configuration!

---

## Quick Checklist

Before testing:

- [ ] Azure Portal redirect URI: `http://localhost:5001/redirect`
- [ ] `.env` file created with redirect URI
- [ ] `MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect` in `.env`
- [ ] All three (Azure, .env, code) match exactly
- [ ] No trailing slash
- [ ] Using `http://` for localhost (not `https://`)
- [ ] Using `localhost` (not `127.0.0.1`)
- [ ] Port is `5001`

If all checked ✅, you're ready to test! 🚀

