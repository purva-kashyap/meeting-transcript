# 📚 Documentation Index

## Quick Start

**🚀 To fix the "Unexpected token '<'" error and start testing:**

```bash
cd /Users/purvakashyap/Projects/meeting-transcript/transcript-summary-app-simpler-rendering
./start_fresh.sh
```

Then open http://localhost:5001 and test the login flow.

---

## 🎯 Your Questions Answered

**Q: Where are we setting the redirect URL?**
**Q: Will it work with real Microsoft Entra?**
**Q: How will the Microsoft login work?**

👉 **Read: [`REDIRECT_URI_GUIDE.md`](./REDIRECT_URI_GUIDE.md)** (15KB)
- Complete explanation of redirect URIs
- Mock vs Production comparison
- Step-by-step production setup
- Azure Portal configuration guide

---

## 📖 Documentation Files

### 🔴 **Essential Reading** (Start Here)

| Document | Size | Purpose |
|----------|------|---------|
| **[README_AUTHENTICATION.md](./README_AUTHENTICATION.md)** | 9.9KB | **Start here!** Overview of the fix and all documentation |
| **[REDIRECT_URI_GUIDE.md](./REDIRECT_URI_GUIDE.md)** | 15KB | **Answers your redirect URI questions** - Mock vs Production |
| **[PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)** | 13KB | **Complete deployment checklist** - Everything you need for production |

### 🟡 **Technical Details** (Deep Dive)

| Document | Size | Purpose |
|----------|------|---------|
| **[AUTHENTICATION_FIX.md](./AUTHENTICATION_FIX.md)** | 6.6KB | Detailed explanation of the authentication bug and fix |
| **[FLOW_DIAGRAMS.md](./FLOW_DIAGRAMS.md)** | 18KB | Visual diagrams of OAuth flows, sessions, before/after |
| **[AUTH_FLOW.md](./AUTH_FLOW.md)** | 10KB | Original authentication flow documentation |

### 🟢 **Reference** (As Needed)

| Document | Size | Purpose |
|----------|------|---------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | 4.2KB | Overall application architecture |
| **[HYBRID_PERMISSIONS.md](./HYBRID_PERMISSIONS.md)** | 6.0KB | Explanation of delegated vs application permissions |
| **[LOGIN_FIX.md](./LOGIN_FIX.md)** | 4.3KB | Previous login flow fixes |
| **[SESSION_CLEANUP.md](./SESSION_CLEANUP.md)** | 2.1KB | Session management and cleanup |
| **[QUICK_FIX_SUMMARY.md](./QUICK_FIX_SUMMARY.md)** | 3.9KB | Quick summary of previous fixes |
| **[README.md](./README.md)** | 4.5KB | Original project README |

### 🔧 **Scripts** (Tools)

| Script | Size | Purpose |
|--------|------|---------|
| **[start_fresh.sh](./start_fresh.sh)** | 351B | Clear sessions and start app (USE THIS!) |
| **[test_auth_flow.sh](./test_auth_flow.sh)** | 1.7KB | Testing guide with instructions |
| **[start.sh](./start.sh)** | 761B | Start app without clearing sessions |

---

## 📋 Reading Path by Goal

### 🎯 Goal: Understand the Fix

1. **[README_AUTHENTICATION.md](./README_AUTHENTICATION.md)** - Overview
2. **[AUTHENTICATION_FIX.md](./AUTHENTICATION_FIX.md)** - Details
3. **[FLOW_DIAGRAMS.md](./FLOW_DIAGRAMS.md)** - Visuals

### 🎯 Goal: Configure Redirect URIs

1. **[REDIRECT_URI_GUIDE.md](./REDIRECT_URI_GUIDE.md)** - Complete guide
   - Where they're set
   - Mock vs Production
   - How OAuth works
   - Common issues

### 🎯 Goal: Deploy to Production

1. **[PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)** - Step-by-step
   - Azure setup (24 steps)
   - Environment configuration
   - Security settings
   - Testing procedures

2. **[REDIRECT_URI_GUIDE.md](./REDIRECT_URI_GUIDE.md)** - Reference for URIs

3. **[HYBRID_PERMISSIONS.md](./HYBRID_PERMISSIONS.md)** - Understand permissions

### 🎯 Goal: Test Locally

1. Run `./start_fresh.sh`
2. Follow instructions in **[test_auth_flow.sh](./test_auth_flow.sh)**
3. Use debug endpoint: http://localhost:5001/debug/session

### 🎯 Goal: Troubleshoot Issues

1. **[FLOW_DIAGRAMS.md](./FLOW_DIAGRAMS.md)** - Understand what should happen
2. **[AUTHENTICATION_FIX.md](./AUTHENTICATION_FIX.md)** - Common issues section
3. **[REDIRECT_URI_GUIDE.md](./REDIRECT_URI_GUIDE.md)** - Redirect URI problems
4. Debug endpoint: http://localhost:5001/debug/session

---

## 🔑 Key Files in Codebase

### Backend (Python)

```
app.py                          # Main Flask application
├─ /auth/login                  # Initiates OAuth flow
├─ /auth/callback               # Handles OAuth callback (PRODUCTION)
├─ /auth/mock-login             # Mock login page (DEVELOPMENT)
├─ /auth/mock-callback          # Mock callback (DEVELOPMENT)
├─ /teams/send-summary          # Send summary to Teams (requires auth)
└─ /debug/session               # Debug endpoint

services/
├─ auth_service.py              # OAuth authentication (MSAL)
├─ graph_service.py             # Microsoft Graph API
├─ zoom_service.py              # Zoom API
└─ llm_service.py               # LLM summary generation
```

### Frontend (Templates)

```
templates/
├─ home.html                    # Landing page
├─ meetings.html                # Meeting list
├─ summary.html                 # Meeting summary (MAIN PAGE)
│  ├─ loginToSend()             # Login function (FIXED)
│  └─ sendToTeams()             # Send summary function
└─ mock_login.html              # Mock Microsoft login (DEVELOPMENT)
```

### Configuration

```
.env                            # Environment variables
├─ USE_MOCK_DATA                # true/false (mock vs production)
├─ MICROSOFT_CLIENT_ID          # Azure app ID
├─ MICROSOFT_CLIENT_SECRET      # Azure app secret
├─ MICROSOFT_TENANT_ID          # Azure tenant ID
└─ MICROSOFT_REDIRECT_URI       # OAuth callback URL ⚠️ IMPORTANT
```

---

## 🐛 Debug Tools

### Debug Endpoint
```
http://localhost:5001/debug/session
```

**Returns:**
```json
{
  "session_data": {
    "authenticated": true/false,
    "user": {"name": "...", "email": "..."},
    "access_token": "...",
    "returnToSummary": {...}
  },
  "is_authenticated": true/false,
  "use_mock_data": true/false,
  "session_id": "..."
}
```

### Clear Sessions
```bash
./start_fresh.sh
# OR
rm -rf flask_session/
```

### Check Session Files
```bash
ls -la flask_session/
cat flask_session/<session-id>
```

---

## 🚦 Current Status

### ✅ What's Working

- ✅ Authentication flow (same-window redirect)
- ✅ Session persistence
- ✅ Mock OAuth for development
- ✅ Production OAuth support (ready, not yet configured)
- ✅ Send to Teams functionality
- ✅ Hybrid permissions (app + delegated)
- ✅ Complete documentation

### ⚠️ What's Next

- ⚠️ Configure Azure App Registration (when ready for production)
- ⚠️ Update `.env` with real credentials
- ⚠️ Test with real Microsoft Entra ID
- ⚠️ Deploy to production environment

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Unexpected token '<'" error | ✅ **FIXED!** Use `./start_fresh.sh` to test |
| Session not persisting | Clear sessions: `rm -rf flask_session/` |
| Login button still showing | Check `/debug/session` - verify `authenticated=true` |
| Redirect URI mismatch | See `REDIRECT_URI_GUIDE.md` - Must match Azure exactly |
| Token expired | Implemented! Uses refresh tokens automatically |

---

## 📞 Need Help?

1. **Check documentation** - Likely answered in one of the guides above
2. **Use debug endpoint** - http://localhost:5001/debug/session
3. **Review flow diagrams** - `FLOW_DIAGRAMS.md` for visual understanding
4. **Check logs** - Flask console output for errors

---

## 📊 Documentation Statistics

- **Total Documentation**: 12 markdown files, 94KB
- **Code Scripts**: 3 shell scripts
- **Coverage**: Development, Testing, Production, Troubleshooting
- **Visual Aids**: Flow diagrams, architecture diagrams, step-by-step guides

---

## 🎯 Summary

### The Fix
Changed authentication from **popup-based** to **same-window redirect** flow.

### Why It Works
Session cookie persists in same browser window throughout OAuth flow.

### Production Ready
Same code works for both mock (development) and production (real Microsoft Entra ID).

### Documentation Complete
Everything you need from understanding the fix to deploying to production.

---

## 🚀 Get Started

```bash
# Test the fix now
./start_fresh.sh

# When ready for production
# 1. Read: PRODUCTION_CHECKLIST.md
# 2. Configure Azure App Registration
# 3. Update .env file
# 4. Deploy!
```

**Happy coding! 🎉**
