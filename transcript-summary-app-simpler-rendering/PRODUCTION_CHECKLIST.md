# Production Deployment Checklist

## Pre-Deployment: Azure Setup

### ☐ 1. Create Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in:
   - **Name**: `Meeting Transcript Summary App`
   - **Supported account types**: 
     - ☐ Single tenant (recommended for internal apps)
     - ☐ Multi-tenant (if supporting multiple organizations)
   - **Redirect URI**: 
     - Platform: **Web**
     - URI: Your production URL (e.g., `https://yourapp.com/auth/callback`)

4. Click **Register**

5. **Copy these values** (you'll need them):
   - ☐ Application (client) ID
   - ☐ Directory (tenant) ID

---

### ☐ 2. Configure API Permissions

**In your app registration:**

1. Go to **API permissions** → **Add a permission** → **Microsoft Graph**

2. **Add Delegated permissions** (for user login):
   - ☐ `User.Read` - Read user profile
   - ☐ `Calendars.Read` - Read user's calendar
   - ☐ `OnlineMeetings.Read` - Read user's meetings
   - ☐ `Chat.ReadWrite` - Read and write chats
   - ☐ `ChatMessage.Send` - Send chat messages

3. **Add Application permissions** (for app-level access):
   - ☐ `Calendars.Read` - Read all calendars
   - ☐ `OnlineMeetings.Read.All` - Read all meetings
   - ☐ `User.Read.All` - Read all user profiles

4. Click **Grant admin consent for [Your Organization]**
   - ☐ Verify all permissions show "Granted"

---

### ☐ 3. Create Client Secret

1. Go to **Certificates & secrets** → **Client secrets** → **New client secret**
2. Description: `Production Secret`
3. Expires: Choose appropriate duration (6 months, 12 months, 24 months)
4. Click **Add**
5. **⚠️ Copy the secret value immediately!** (Won't be shown again)
   - ☐ Client secret value copied

---

### ☐ 4. Configure Redirect URIs

1. Go to **Authentication** → **Platform configurations** → **Web**

2. Add all necessary redirect URIs:
   - ☐ Development: `http://localhost:5001/auth/callback`
   - ☐ Staging: `https://staging.yourapp.com/auth/callback` (if applicable)
   - ☐ Production: `https://yourapp.com/auth/callback`

3. **Important**: Remove `http://` URIs before production launch (except localhost)

4. **Implicit grant and hybrid flows**:
   - ☐ Leave unchecked (we're using authorization code flow)

5. Click **Save**

---

### ☐ 5. Configure Token Settings (Optional but Recommended)

1. Go to **Token configuration**
2. Add optional claims if needed:
   - ☐ `email` - Include email in ID token
   - ☐ `preferred_username` - Include username

---

## Application Configuration

### ☐ 6. Environment Variables

Create production `.env` file:

```bash
# Application Mode
USE_MOCK_DATA=false  # ⚠️ CRITICAL: Set to false for production

# Microsoft Azure Configuration
MICROSOFT_CLIENT_ID=<paste-client-id-here>
MICROSOFT_CLIENT_SECRET=<paste-secret-here>
MICROSOFT_TENANT_ID=<paste-tenant-id-here>
MICROSOFT_REDIRECT_URI=https://yourapp.com/auth/callback
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/<tenant-id>

# Microsoft Graph API
GRAPH_BASE_URL=https://graph.microsoft.com/v1.0

# Zoom Configuration (if using)
ZOOM_BASE_URL=https://api.zoom.us
ZOOM_CLIENT_ID=<your-zoom-client-id>
ZOOM_CLIENT_SECRET=<your-zoom-client-secret>

# Flask Configuration
FLASK_SECRET_KEY=<generate-strong-random-key>
FLASK_ENV=production
FLASK_DEBUG=false

# Session Configuration
SESSION_TYPE=redis  # or 'filesystem' for single-server
SESSION_PERMANENT=false
SESSION_USE_SIGNER=true
SESSION_KEY_PREFIX=transcript_app:

# Redis Configuration (if using)
REDIS_URL=redis://localhost:6379/0

# Database Configuration (if using)
# DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security Headers
SESSION_COOKIE_SECURE=true  # Requires HTTPS
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

**Checklist:**
- ☐ `USE_MOCK_DATA=false` confirmed
- ☐ All Microsoft credentials filled
- ☐ Redirect URI matches Azure configuration
- ☐ Strong secret key generated (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
- ☐ Session security settings enabled

---

### ☐ 7. Generate Strong Secret Key

Run this command to generate a secure Flask secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it for `FLASK_SECRET_KEY`.

- ☐ Secret key generated and added to `.env`

---

### ☐ 8. Update App Configuration (app.py)

Ensure these settings are production-ready:

```python
# In app.py
app.config.update(
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true',
    SESSION_COOKIE_HTTPONLY=os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true',
    SESSION_COOKIE_SAMESITE=os.getenv('SESSION_COOKIE_SAMESITE', 'Lax'),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
)
```

- ☐ Security settings configured
- ☐ Session lifetime appropriate

---

## Infrastructure Setup

### ☐ 9. HTTPS Certificate

**Production MUST use HTTPS!** Microsoft will reject `http://` redirect URIs.

**Options:**

**A. Let's Encrypt (Free)**
```bash
sudo certbot --nginx -d yourapp.com -d www.yourapp.com
```
- ☐ Certificate installed
- ☐ Auto-renewal configured

**B. Cloud Provider Certificate**
- ☐ Azure App Service: Configure custom domain + managed certificate
- ☐ AWS: Use AWS Certificate Manager (ACM)
- ☐ Heroku: SSL certificate add-on

**C. CloudFlare**
- ☐ Enable CloudFlare proxy
- ☐ SSL set to "Full" or "Full (strict)"

---

### ☐ 10. Session Storage (Production)

For multi-server deployments, use **Redis** or **Database** for sessions:

**Option A: Redis (Recommended)**

```python
# requirements.txt
redis==5.0.0
flask-session==0.5.0

# app.py
from redis import Redis
import os

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis.from_url(
    os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)
```

- ☐ Redis server deployed
- ☐ Connection string configured
- ☐ Session storage tested

**Option B: Database**

```python
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
```

- ☐ Database deployed
- ☐ Session table created
- ☐ Connection tested

---

### ☐ 11. Deployment Platform Setup

**Choose your platform:**

#### **Azure App Service**
- ☐ Create App Service Plan
- ☐ Create Web App
- ☐ Configure environment variables in **Configuration** → **Application settings**
- ☐ Enable HTTPS Only
- ☐ Configure custom domain (optional)
- ☐ Deploy code (GitHub Actions, Azure DevOps, or FTP)

#### **Heroku**
```bash
heroku create yourapp
heroku config:set USE_MOCK_DATA=false
heroku config:set MICROSOFT_CLIENT_ID=...
heroku config:set MICROSOFT_CLIENT_SECRET=...
# ... set all other env vars
git push heroku main
```
- ☐ App created
- ☐ Environment variables set
- ☐ Code deployed

#### **AWS Elastic Beanstalk**
- ☐ Create Elastic Beanstalk application
- ☐ Configure environment variables
- ☐ Deploy application
- ☐ Configure SSL certificate

#### **Docker**
- ☐ Build Docker image
- ☐ Push to registry
- ☐ Deploy to Kubernetes/ECS/other
- ☐ Configure environment variables
- ☐ Set up ingress/load balancer with SSL

---

## Testing

### ☐ 12. Test OAuth Flow

**Test with real Microsoft account:**

1. ☐ Navigate to your production URL
2. ☐ Click "Login to Post in Teams"
3. ☐ Redirected to Microsoft login
4. ☐ Enter Microsoft credentials
5. ☐ See consent screen with all requested permissions
6. ☐ Click "Accept"
7. ☐ Redirected back to your app successfully
8. ☐ User info displayed correctly
9. ☐ "Send in Teams" button appears

**If any step fails:**
- Check Azure App Registration redirect URI
- Verify client ID and secret
- Check browser console for errors
- Review Flask logs

---

### ☐ 13. Test API Functionality

**Test Teams Integration:**

1. ☐ List Teams meetings (application permissions)
2. ☐ View meeting transcript
3. ☐ Generate summary
4. ☐ Send summary to Teams chat (delegated permissions)
5. ☐ Verify message appears in Teams

**Test Zoom Integration (if enabled):**

1. ☐ List Zoom recordings
2. ☐ Get transcript
3. ☐ Generate summary

---

### ☐ 14. Security Testing

- ☐ HTTPS enforced (no HTTP access)
- ☐ Session cookies marked `Secure` and `HttpOnly`
- ☐ CSRF protection working (state parameter validated)
- ☐ No sensitive data in logs
- ☐ Client secret not exposed in frontend
- ☐ Error messages don't leak sensitive info

---

### ☐ 15. Performance Testing

- ☐ Load test with multiple concurrent users
- ☐ Session storage handles traffic
- ☐ API rate limits configured (if needed)
- ☐ Response times acceptable

---

## Monitoring & Maintenance

### ☐ 16. Logging

Configure application logging:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

- ☐ Logging configured
- ☐ Log rotation set up
- ☐ Error tracking integrated (Sentry, Azure Monitor, etc.)

---

### ☐ 17. Monitoring

Set up monitoring:

- ☐ Application uptime monitoring
- ☐ API endpoint health checks
- ☐ Error rate alerts
- ☐ Performance metrics
- ☐ Session storage health

**Tools:**
- Azure Application Insights
- DataDog
- New Relic
- Prometheus + Grafana

---

### ☐ 18. Backup & Recovery

- ☐ Database backups (if using)
- ☐ Session data backup strategy
- ☐ Configuration backup
- ☐ Disaster recovery plan documented

---

## Documentation

### ☐ 19. User Documentation

- ☐ User guide created
- ☐ Login instructions
- ☐ Feature documentation
- ☐ Troubleshooting guide

---

### ☐ 20. Admin Documentation

- ☐ Deployment procedure documented
- ☐ Environment variables documented
- ☐ Azure configuration documented
- ☐ Rollback procedure documented
- ☐ Maintenance procedures documented

---

## Compliance & Legal

### ☐ 21. Privacy & Compliance

- ☐ Privacy policy created
- ☐ Terms of service created
- ☐ Data retention policy defined
- ☐ GDPR compliance (if applicable)
- ☐ User consent flows implemented

---

### ☐ 22. Security Review

- ☐ Penetration testing completed
- ☐ Security audit passed
- ☐ Vulnerability scan completed
- ☐ Dependencies updated

---

## Post-Deployment

### ☐ 23. Verify Production

After deployment:

1. ☐ All environment variables loaded correctly
2. ☐ OAuth flow works end-to-end
3. ☐ Teams integration functional
4. ☐ Zoom integration functional (if enabled)
5. ☐ Sessions persisting correctly
6. ☐ No errors in logs
7. ☐ SSL certificate valid
8. ☐ Monitoring active

---

### ☐ 24. Client Secret Rotation Plan

**Important:** Client secrets expire!

- ☐ Set calendar reminder for secret expiration
- ☐ Document secret rotation procedure
- ☐ Test secret rotation in staging first

**Rotation Procedure:**
1. Create new client secret in Azure Portal (keep old one active)
2. Update production `.env` with new secret
3. Restart application
4. Test OAuth flow
5. Delete old secret in Azure Portal

---

## Common Issues & Solutions

### Issue: "AADSTS50011: Reply URL mismatch"

**Solution:**
- ☐ Verify redirect URI in `.env` matches Azure Portal exactly
- ☐ Check for http vs https
- ☐ Check for trailing slashes
- ☐ Restart application after changing `.env`

### Issue: Sessions not persisting

**Solution:**
- ☐ Check `FLASK_SECRET_KEY` is set
- ☐ Verify session storage is accessible (Redis/Database)
- ☐ Check cookie settings (Secure, SameSite)
- ☐ Ensure HTTPS is enabled

### Issue: "Invalid client secret"

**Solution:**
- ☐ Regenerate secret in Azure Portal
- ☐ Update `.env` immediately
- ☐ Restart application

### Issue: Consent screen not showing permissions

**Solution:**
- ☐ Check API permissions in Azure Portal
- ☐ Grant admin consent
- ☐ Wait a few minutes for propagation

---

## Final Pre-Launch Checklist

- ☐ All environment variables set correctly
- ☐ `USE_MOCK_DATA=false` confirmed
- ☐ HTTPS working
- ☐ OAuth flow tested successfully
- ☐ Teams integration tested
- ☐ Error handling working
- ☐ Logging configured
- ☐ Monitoring active
- ☐ Documentation complete
- ☐ Backup strategy in place
- ☐ Security review passed

---

## Launch! 🚀

Once all items are checked:

1. ☐ Announce to users
2. ☐ Monitor logs closely for first 24 hours
3. ☐ Be ready for user support
4. ☐ Collect feedback

**Congratulations on your production deployment!** 🎉
