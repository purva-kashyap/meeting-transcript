# Azure App Registration Quick Start Guide

## 📋 Prerequisites
- Azure account with admin access to Azure Active Directory
- Permissions to create app registrations and grant consent

---

## 🚀 Step-by-Step Setup (5 minutes)

### Step 1: Create App Registration

1. Go to **Azure Portal** (https://portal.azure.com)
2. Navigate to **Azure Active Directory**
3. Click **App registrations** in left menu
4. Click **+ New registration**

**Fill in the form:**
- **Name**: `Meeting Transcript Summary App` (or any name you prefer)
- **Supported account types**: 
  - Choose **"Accounts in this organizational directory only"** (single tenant)
  - OR **"Accounts in any organizational directory"** (multi-tenant)
- **Redirect URI**:
  - Platform: **Web**
  - URI: `http://localhost:5001/redirect`
  - For production, add: `https://your-domain.com/redirect`

5. Click **Register**

✅ **Result**: App is created. You should see the Overview page.

---

### Step 2: Copy Application (Client) ID

On the **Overview** page:

1. Find **Application (client) ID**
2. Click the copy icon
3. Save it for your `.env` file

```
MICROSOFT_CLIENT_ID=<paste-here>
```

---

### Step 3: Copy Directory (Tenant) ID

Still on the **Overview** page:

1. Find **Directory (tenant) ID**
2. Click the copy icon
3. Save it for your `.env` file

```
MICROSOFT_TENANT_ID=<paste-here>
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/<paste-tenant-id-here>
```

---

### Step 4: Create Client Secret

1. In left menu, click **Certificates & secrets**
2. Click **+ New client secret**
3. **Description**: `Meeting App Secret` (or any description)
4. **Expires**: Choose duration (6 months, 12 months, or 24 months recommended)
5. Click **Add**

⚠️ **IMPORTANT**: Copy the **Value** immediately (the secret value will be hidden after you leave this page!)

```
MICROSOFT_CLIENT_SECRET=<paste-secret-value-here>
```

---

### Step 5: Add API Permissions (Delegated)

1. In left menu, click **API permissions**
2. You should see **User.Read** already added (this is default)
3. Click **+ Add a permission**

**For each permission below:**
- Click **Microsoft Graph**
- Click **Delegated permissions**
- Search for the permission
- Check the box
- Click **Add permissions**

**Permissions to add:**

| Permission | Purpose |
|------------|---------|
| ✅ **User.Read** | Already added - Read user profile |
| ➕ **Calendars.Read** | Read calendar events |
| ➕ **OnlineMeetings.Read** | Access online meeting data |
| ➕ **Chat.ReadWrite** | Create and manage chats |
| ➕ **ChatMessage.Send** | Send messages to chats |

After adding all permissions, you should see:
```
Microsoft Graph (5)
  User.Read                 Delegated   Admin consent required
  Calendars.Read           Delegated   Admin consent required
  OnlineMeetings.Read      Delegated   Admin consent required
  Chat.ReadWrite           Delegated   Admin consent required
  ChatMessage.Send         Delegated   Admin consent required
```

---

### Step 6: Grant Admin Consent

⚠️ **Important**: This step requires admin privileges.

**If you're an admin:**
1. Click **✅ Grant admin consent for [Your Organization]**
2. Click **Yes** in the confirmation dialog
3. Wait for green checkmarks to appear next to all permissions

**If you're not an admin:**
- Users will be prompted to consent when they first log in
- Each user must individually consent to these permissions
- Contact your admin to grant organization-wide consent

✅ **Result**: Status column should show "Granted for [Your Organization]"

---

### Step 7: Verify Redirect URI

1. In left menu, click **Authentication**
2. Under **Platform configurations** → **Web**, verify:
   - `http://localhost:5001/redirect` is listed
3. (Optional) For production, click **+ Add URI**:
   - Add: `https://your-domain.com/redirect`

**Advanced settings** (optional but recommended):
- **Access tokens**: ☐ (unchecked)
- **ID tokens**: ☐ (unchecked)
- We're using authorization code flow, not implicit flow

---

## 📝 Complete .env Configuration

Now create your `.env` file:

```bash
cd transcript-summary-delegated
cp .env.example .env
nano .env  # or use your preferred editor
```

**Fill in these values:**

```bash
# CRITICAL: Set to false to use real APIs
USE_MOCK_DATA=false

# Microsoft Graph API Configuration
GRAPH_BASE_URL=https://graph.microsoft.com/v1.0
MICROSOFT_CLIENT_ID=<from-step-2>
MICROSOFT_CLIENT_SECRET=<from-step-4>
MICROSOFT_TENANT_ID=<from-step-3>
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/<from-step-3>
MICROSOFT_REDIRECT_URI=http://localhost:5001/redirect

# Flask Configuration
FLASK_SECRET_KEY=<generate-below>
FLASK_ENV=development

# Session Configuration
SESSION_TYPE=filesystem
SESSION_PERMANENT=False
```

**Generate Flask secret key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as `FLASK_SECRET_KEY`.

---

## ✅ Verification Checklist

Before running the app, verify:

- [ ] App registration created in Azure Portal
- [ ] Application (client) ID copied to `.env`
- [ ] Directory (tenant) ID copied to `.env`
- [ ] Client secret created and copied to `.env` (⚠️ won't be shown again!)
- [ ] 5 delegated permissions added (User.Read, Calendars.Read, OnlineMeetings.Read, Chat.ReadWrite, ChatMessage.Send)
- [ ] Admin consent granted (green checkmarks visible)
- [ ] Redirect URI configured: `http://localhost:5001/redirect`
- [ ] `.env` file created with all values filled in
- [ ] Flask secret key generated and added to `.env`
- [ ] `USE_MOCK_DATA=false` set in `.env`

---

## 🚀 Test the Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the app:**
```bash
python app.py
```

3. **Open browser:**
```
http://localhost:5001
```

4. **Test authentication:**
- Click "Show Teams Meetings"
- You'll be redirected to Microsoft login
- Sign in with your organizational account
- (First time) You may see consent screen - click "Accept"
- You should be redirected back to the app
- You should see your Teams meetings!

---

## 🐛 Troubleshooting

### "Invalid client secret"
- **Cause**: Client secret was not copied correctly or has expired
- **Fix**: Generate new client secret in Azure Portal, update `.env`

### "Redirect URI mismatch"
- **Cause**: Redirect URI in Azure doesn't match what's in `.env`
- **Fix**: Verify both are exactly `http://localhost:5001/redirect`

### "Insufficient privileges to complete the operation"
- **Cause**: Permissions not granted or admin consent not given
- **Fix**: Go to API Permissions, click "Grant admin consent"

### "User cannot consent"
- **Cause**: Your organization requires admin consent for these permissions
- **Fix**: Contact your Azure AD admin to grant consent

### "State mismatch error"
- **Cause**: Session cookie issue or CSRF protection triggered
- **Fix**: Clear browser cookies, try again. Check session configuration in app.py

### Can't see any meetings
- **Cause**: Graph API endpoint might not be correct
- **Fix**: Check terminal logs for Graph API errors. May need to adjust endpoints in `graph_service.py`

---

## 📞 Getting Help

If you encounter issues:

1. **Check terminal logs** - detailed error messages are logged
2. **Check browser console** - look for JavaScript errors
3. **Verify Azure setup** - compare with this guide step-by-step
4. **Check `.env` file** - ensure no typos, no extra spaces
5. **Test permissions** - try Microsoft Graph Explorer (https://developer.microsoft.com/graph/graph-explorer) to test permissions independently

---

## 🔒 Security Best Practices

### Development
- ✅ Use `http://localhost:5001` (HTTP is OK for local dev)
- ✅ Keep client secret in `.env` file (not committed to git)
- ✅ Use separate app registration for dev and production

### Production
- ⚠️ Change to `https://your-domain.com` (HTTPS required!)
- ⚠️ Set `FLASK_ENV=production` in `.env`
- ⚠️ Set `SESSION_COOKIE_SECURE=True` (automatically enabled for production in code)
- ⚠️ Use Azure Key Vault or AWS Secrets Manager for secrets
- ⚠️ Create separate app registration for production
- ⚠️ Set shorter client secret expiration (3-6 months)
- ⚠️ Monitor and rotate secrets regularly

---

## 📊 Expected Results

### First Login
1. User clicks "Show Teams Meetings"
2. Redirected to `login.microsoftonline.com`
3. User enters credentials
4. (First time only) Consent screen appears with 5 permissions listed
5. User clicks "Accept"
6. Redirected back to `http://localhost:5001/meetings.html`
7. Teams meetings are displayed

### Subsequent Logins
1. User clicks "Show Teams Meetings"
2. If already authenticated: immediately shows meetings
3. If session expired: quick redirect to Microsoft and back (no consent screen)
4. Teams meetings are displayed

---

## 🎉 Success!

Once you see your Teams meetings in the app, you've successfully:
- ✅ Configured Azure App Registration
- ✅ Set up delegated permissions
- ✅ Configured the Flask app
- ✅ Authenticated with Microsoft
- ✅ Made your first Graph API call!

**Next steps:**
- Test viewing meeting transcripts
- Test sending summary to Teams chat
- Monitor logs for any issues
- Fine-tune Graph API endpoints based on your data

---

## 🔗 Useful Links

- [Azure Portal](https://portal.azure.com)
- [Microsoft Graph Explorer](https://developer.microsoft.com/graph/graph-explorer) - Test Graph API calls
- [Graph API Permissions Reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Azure AD App Registration Guide](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)

