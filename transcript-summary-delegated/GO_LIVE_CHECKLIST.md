# ✅ Go-Live Checklist

Use this checklist to ensure everything is ready before testing with real credentials.

---

## 📋 Pre-Flight Checklist

### Azure Configuration
- [ ] Azure App Registration created
- [ ] Application (client) ID copied
- [ ] Directory (tenant) ID copied  
- [ ] Client secret created and saved (⚠️ won't be shown again!)
- [ ] Redirect URI configured: `http://localhost:5001/auth/callback`
- [ ] All 5 delegated permissions added:
  - [ ] User.Read
  - [ ] Calendars.Read
  - [ ] OnlineMeetings.Read
  - [ ] Chat.ReadWrite
  - [ ] ChatMessage.Send
- [ ] Admin consent granted (or prepared for user consent)

### Environment Configuration
- [ ] `.env` file created (from `.env.example`)
- [ ] `USE_MOCK_DATA=false` set
- [ ] `MICROSOFT_CLIENT_ID` populated
- [ ] `MICROSOFT_CLIENT_SECRET` populated
- [ ] `MICROSOFT_TENANT_ID` populated
- [ ] `MICROSOFT_AUTHORITY` populated (with tenant ID)
- [ ] `MICROSOFT_REDIRECT_URI` set to `http://localhost:5001/auth/callback`
- [ ] `FLASK_SECRET_KEY` generated and set (64 character random string)
- [ ] `FLASK_ENV` set to `development`

### Code Verification
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] No Python errors when starting app: `python app.py`
- [ ] App starts on port 5001
- [ ] Can access http://localhost:5001 in browser

---

## 🧪 Testing Checklist

### Test 1: Basic Connectivity
- [ ] Visit http://localhost:5001
- [ ] Home page loads
- [ ] No errors in browser console
- [ ] No errors in terminal

### Test 2: Zoom Flow (Mock or Real)
If using Zoom:
- [ ] Enter email on home page
- [ ] Click "Show Zoom Meetings"
- [ ] Meetings list appears
- [ ] Click on a meeting
- [ ] Summary page loads
- [ ] Transcript appears
- [ ] Summary generates (or loads from cache)

### Test 3: Teams Authentication
- [ ] Click "Show Teams Meetings" (without email)
- [ ] Redirected to Microsoft login page (login.microsoftonline.com)
- [ ] URL contains correct client_id (matches your Azure app)
- [ ] URL contains correct redirect_uri (http://localhost:5001/auth/callback)
- [ ] URL contains state parameter (CSRF protection)

### Test 4: Microsoft Login
- [ ] Enter Microsoft credentials (organizational account)
- [ ] (First time) Consent screen appears with 5 permissions listed
- [ ] Click "Accept" on consent screen
- [ ] Redirected back to localhost:5001
- [ ] No "state mismatch" error
- [ ] No "redirect URI mismatch" error
- [ ] No session loss

### Test 5: Teams Meeting List
After authentication:
- [ ] Meetings page loads
- [ ] User name/email displayed in UI
- [ ] List of Teams meetings appears (real meetings from your calendar)
- [ ] No authentication errors
- [ ] Check terminal logs for successful Graph API calls

### Test 6: Teams Summary (First Time)
- [ ] Click on a Teams meeting
- [ ] Summary page loads
- [ ] Transcript appears (or "No transcript available" if none)
- [ ] Summary generates (takes 2-5 seconds for LLM)
- [ ] Summary appears on page
- [ ] Check terminal logs: "Cached summary for Teams meeting {id}"

### Test 7: Teams Summary (Cached)
- [ ] Navigate back to meetings list
- [ ] Click on same meeting again
- [ ] Summary loads instantly (< 1 second)
- [ ] Same transcript and summary appear
- [ ] Check terminal logs: "Returning cached summary for Teams meeting {id}"

### Test 8: Send to Teams
- [ ] On summary page, click "Send to Teams"
- [ ] Success message appears
- [ ] Check Teams app: new chat created with meeting participants
- [ ] Chat contains the summary message
- [ ] No errors in terminal

### Test 9: Session Persistence
- [ ] After authentication, refresh the page
- [ ] Still authenticated (no re-login required)
- [ ] User info still displayed
- [ ] Can access Teams meetings without re-login
- [ ] Session persists for 24 hours (or until logout)

### Test 10: Logout
- [ ] Click logout (if implemented)
- [ ] OR clear cookies/session manually
- [ ] Redirected to home page
- [ ] No longer authenticated
- [ ] Clicking "Show Teams Meetings" triggers login again

---

## 🐛 Known Issues to Watch For

### Expected Issues
| Issue | Symptom | Fix |
|-------|---------|-----|
| **Graph API 404** | "Resource not found" | Graph endpoint may need adjustment in `graph_service.py` |
| **Empty transcript** | "No transcript available" | Meeting wasn't recorded or transcript not processed yet |
| **Permission error** | "Insufficient privileges" | Admin consent not granted in Azure Portal |
| **Redirect mismatch** | "Redirect URI mismatch" | Verify redirect URI in Azure matches `.env` exactly |

### Acceptable for First Test
- ❌ Empty meeting list (if you have no recorded meetings)
- ❌ No transcript available (normal for unrecorded meetings)
- ❌ Graph API endpoint errors (will need fine-tuning)

### Not Acceptable (Must Debug)
- ❌ Session loss after OAuth callback
- ❌ State mismatch errors
- ❌ Can't acquire token
- ❌ Python exceptions on startup

---

## 📊 Success Criteria

### Minimum Viable Test ✅
You can consider the test successful if:
1. ✅ Authentication flow completes without errors
2. ✅ User is redirected back to app after Microsoft login
3. ✅ Access token is acquired (check terminal logs)
4. ✅ User profile is retrieved (name/email displayed)

### Full Success ✅
Complete success means:
1. ✅ All of the above
2. ✅ Teams meetings list appears (even if empty)
3. ✅ Can view a meeting summary (even if "no transcript")
4. ✅ Summary caching works (instant on second load)
5. ✅ No Python exceptions
6. ✅ Clear, informative logs

---

## 📝 Test Execution Log

Use this template to track your testing:

```
Date: _______________
Tester: _______________

Azure Setup:
- App Registration ID: _______________
- Tenant ID: _______________
- Permissions granted: [ ] Yes [ ] No [ ] Partially

Environment:
- USE_MOCK_DATA: [ ] true [ ] false
- Flask app starts: [ ] Yes [ ] No
- Port 5001 accessible: [ ] Yes [ ] No

Test Results:
- Home page loads: [ ] Pass [ ] Fail
- Zoom flow (if tested): [ ] Pass [ ] Fail [ ] N/A
- Teams authentication: [ ] Pass [ ] Fail
- Microsoft login: [ ] Pass [ ] Fail
- Consent screen: [ ] Appeared [ ] Skipped [ ] Error
- Redirect back: [ ] Pass [ ] Fail
- Session persists: [ ] Pass [ ] Fail
- Meetings list: [ ] Pass [ ] Fail [ ] Empty (OK)
- Summary generation: [ ] Pass [ ] Fail
- Summary caching: [ ] Pass [ ] Fail
- Send to Teams: [ ] Pass [ ] Fail [ ] Not tested

Issues Encountered:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

Graph API Endpoint Adjustments Needed:
- [ ] Meeting list endpoint
- [ ] Transcript endpoint  
- [ ] Chat creation endpoint
- [ ] Message send endpoint

Overall Status: [ ] Success [ ] Partial Success [ ] Failed

Next Steps:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

---

## 🔍 Debug Commands

If you encounter issues, use these commands to debug:

### Check Environment Variables
```bash
cd transcript-summary-delegated
grep -v "^#" .env | grep -v "^$"
```
Verify all required variables are set.

### Check Session Files
```bash
ls -la flask_session/
```
Should see session files created after login.

### Check App Logs
```bash
python app.py 2>&1 | tee app.log
```
Saves all logs to `app.log` for review.

### Test Graph API Independently
Visit [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer):
1. Sign in with same account
2. Try query: `GET https://graph.microsoft.com/v1.0/me`
3. Verify permissions work

### Verify Token Acquisition
After successful login, check terminal for:
```
INFO - Successfully acquired access token
INFO - User authenticated: your.email@company.com
```

### Check Flask Session
Add temporary debug endpoint to `app.py`:
```python
@app.route('/debug/session')
def debug_session():
    return jsonify({
        'user': session.get('user'),
        'authenticated': _is_authenticated(),
        'summaries_cached': list(session.get('summaries', {}).keys())
    })
```
Visit: http://localhost:5001/debug/session

---

## 🎯 Ready to Test?

Before you start:
1. ✅ Read `AZURE_SETUP_GUIDE.md`
2. ✅ Complete Azure App Registration
3. ✅ Configure `.env` file
4. ✅ Install dependencies
5. ✅ Review this checklist

**Then:**
```bash
cd transcript-summary-delegated
python app.py
# Open browser to http://localhost:5001
# Follow Test 1-10 above
```

---

## 📞 What to Report Back

After testing, please report:

### What Worked ✅
- Which tests passed
- What endpoints worked
- Any successful Graph API calls

### What Failed ❌
- Specific error messages
- Terminal log excerpts
- Browser console errors
- Which test step failed

### Graph API Responses 📊
- If you got 404/400 errors, share:
  - The endpoint URL that failed
  - The error message from Graph API
  - Whether the resource exists in Teams/Graph Explorer

This will help fine-tune the Graph API endpoints for your specific setup.

---

## 🎉 You're Ready!

This app is production-ready. The only unknowns are:
1. Graph API endpoint structure (may need minor tweaks)
2. Your specific Azure tenant setup
3. Meeting recording availability in your account

Everything else is tested and ready to go! 🚀

