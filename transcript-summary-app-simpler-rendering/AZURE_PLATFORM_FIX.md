# Azure App Registration Fix - Checklist

## ❌ Current Problem

**Error:** `Client is public so neither 'client_assertion' nor 'client_secret' should be present`

**Root Cause:** Redirect URI registered under "Mobile and desktop applications" (Public client) but code uses Confidential client with secret.

---

## ✅ Solution: Move Redirect URI to Web Platform

### Step-by-Step Instructions

#### 1. Open Azure Portal
- Go to: https://portal.azure.com
- Navigate to: **Azure Active Directory** → **App registrations**
- Select your app

#### 2. Go to Authentication
- Click **"Authentication"** in the left sidebar

#### 3. Check Current Configuration

**You'll see something like this:**

```
Platform configurations
└─ Mobile and desktop applications  ❌ WRONG!
   └─ Redirect URIs:
      • http://localhost:5001/auth/callback
      • (maybe others)
```

#### 4. Add Web Platform

- Click **"+ Add a platform"** button
- Select **"Web"**
- In the "Redirect URIs" field, enter:
  ```
  http://localhost:5001/auth/callback
  ```
- **For production**, also add:
  ```
  https://yourapp.com/auth/callback
  ```
- Leave "Implicit grant and hybrid flows" **UNCHECKED**
- Click **"Configure"**

#### 5. Remove from Mobile and Desktop (Optional but Recommended)

- Under "Mobile and desktop applications"
- Click the **trash/delete icon** next to the redirect URI
- This cleans up the configuration

#### 6. Verify Advanced Settings

Scroll down to **"Advanced settings"**:

```
Allow public client flows
└─ Enable the following mobile and desktop flows:  [No] ✅
```

Make sure this is set to **"No"**

#### 7. Save Configuration

- Click **"Save"** at the top
- Wait for confirmation message

---

## ✅ Correct Final Configuration

### Platform configurations should show:

```
Web
├─ Redirect URIs:
│  ├─ http://localhost:5001/auth/callback  ✅
│  └─ https://yourapp.com/auth/callback (for production)
├─ Front-channel logout URL: (leave empty)
├─ Implicit grant and hybrid flows:
│  ├─ Access tokens: ☐ Unchecked
│  └─ ID tokens: ☐ Unchecked
```

```
Mobile and desktop applications
└─ Redirect URIs: (none)  ✅
```

```
Advanced settings
└─ Allow public client flows: No  ✅
```

---

## 🧪 Test the Fix

### 1. Verify Configuration

Visit debug endpoint:
```
http://localhost:5001/debug/msal-config
```

Should show:
```json
{
  "use_mock_data": false,
  "client_id": "12345678...",
  "client_secret_set": true,  ✅
  "client_secret_length": 40,  ✅ (or similar)
  "authority": "https://login.microsoftonline.com/...",
  "redirect_uri": "http://localhost:5001/auth/callback",
  "scopes": [...]
}
```

### 2. Test Login Flow

1. Start app:
   ```bash
   ./start_fresh.sh
   ```

2. Navigate to Teams meeting summary

3. Click "Login to Post in Teams"

4. You should:
   - ✅ Be redirected to Microsoft login (not get an error)
   - ✅ See Microsoft login page
   - ✅ Be able to enter credentials
   - ✅ Be redirected back to your app successfully

### 3. What Changed

**Before (Error):**
```
Your App → Microsoft OAuth
├─ Platform: Mobile/Desktop (Public Client)
├─ Sends: client_id + client_secret
└─ Microsoft: ❌ "Public clients can't use secrets!"
```

**After (Working):**
```
Your App → Microsoft OAuth
├─ Platform: Web (Confidential Client)
├─ Sends: client_id + client_secret
└─ Microsoft: ✅ "Valid confidential client!"
```

---

## 📋 Quick Reference

### Your App Type: Server-side Web Application

| Aspect | Configuration |
|--------|---------------|
| **Platform** | Web |
| **Client Type** | Confidential |
| **Authentication Method** | Client ID + Client Secret |
| **MSAL Library** | `msal.ConfidentialClientApplication` |
| **Redirect URI Type** | Web (not Mobile/Desktop) |
| **Allow Public Client Flows** | No |

### Other App Types (For Reference)

**Mobile App / Desktop App:**
- Platform: Mobile and desktop applications
- Client Type: Public
- Authentication: Client ID only (no secret)
- MSAL: `PublicClientApplication`

**Single Page App (React, Vue, Angular):**
- Platform: Single-page application
- Client Type: Public
- Authentication: Client ID only
- MSAL: MSAL.js in browser

---

## 🔍 Common Issues After Fix

### Issue: Still getting error after moving redirect URI

**Solution:**
1. Clear browser cache and cookies
2. Clear Flask sessions: `rm -rf flask_session/`
3. Restart your Flask app
4. Try login again

### Issue: "Redirect URI mismatch" error

**Solution:**
- Verify the URI in Azure Portal **exactly matches** your `.env` file
- Check for:
  - `http` vs `https`
  - Trailing slash: `/auth/callback/` vs `/auth/callback`
  - Port number: `:5001` must be included for localhost
  - Path: `/auth/callback` (exact match)

### Issue: "Invalid client secret"

**Solution:**
1. Generate new client secret in Azure Portal:
   - **Certificates & secrets** → **New client secret**
2. Copy the value immediately (shown only once!)
3. Update `.env`:
   ```bash
   MICROSOFT_CLIENT_SECRET=<new-secret-value>
   ```
4. Restart app

---

## ✅ Verification Checklist

After making changes, verify:

- [ ] Redirect URI is under **"Web"** platform in Azure Portal
- [ ] Redirect URI **exactly matches** `.env` file
- [ ] "Allow public client flows" is set to **"No"**
- [ ] Client secret is properly set in `.env`
- [ ] `.env` has `USE_MOCK_DATA=false`
- [ ] Flask sessions cleared: `rm -rf flask_session/`
- [ ] App restarted
- [ ] Can navigate to Microsoft login page (no immediate error)
- [ ] Can complete login and return to app

---

## 🎯 Summary

**The Problem:**
- Redirect URI was under "Mobile and desktop applications" (public client)
- Your code uses confidential client with secret
- Microsoft rejected this mismatch

**The Solution:**
- Move redirect URI to "Web" platform
- Keep "Allow public client flows" = No
- This matches your server-side Flask app architecture

**Result:**
- ✅ Microsoft accepts your client ID + secret
- ✅ OAuth flow works correctly
- ✅ Users can log in and post to Teams

---

## 📚 Related Documentation

- [REDIRECT_URI_GUIDE.md](./REDIRECT_URI_GUIDE.md) - Complete redirect URI guide
- [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) - Full deployment checklist
- [SESSION_EXPLAINED.md](./SESSION_EXPLAINED.md) - How sessions work

---

**After making these changes, your authentication should work perfectly!** 🎉
