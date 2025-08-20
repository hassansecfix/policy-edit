# Deploy Flask API to Render - Detailed Guide

## Overview

Render is a cloud platform that makes it easy to deploy web services. It offers a free tier perfect for your Flask API backend.

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Push your code to GitHub** (if not already done):

   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Ensure your Flask app is configured for production** (already done in your project):
   - ✅ CORS headers configured
   - ✅ Environment variables support
   - ✅ Requirements.txt present

### Step 2: Create Render Account

1. **Go to [render.com](https://render.com)**
2. **Click "Get Started for Free"**
3. **Sign up** using:
   - GitHub account (recommended)
   - Google account
   - Email address

### Step 3: Connect Your Repository

1. **From Render Dashboard**, click **"New +"** button
2. **Select "Web Service"**
3. **Connect your GitHub account** if not already connected
4. **Find and select your repository** (`policy-edit`)
5. **Click "Connect"**

### Step 4: Configure Your Web Service

#### Basic Configuration:

```
Name: policy-automation-api
Environment: Python 3
Region: Oregon (US West) or closest to you
Branch: main
```

#### Build & Deploy Settings:

```
Root Directory: web_ui
Build Command: pip install -r requirements.txt
Start Command: python3 app.py
```

#### Instance Type:

```
Free ($0/month) - Perfect for development/testing
```

### Step 5: Environment Variables

Click **"Advanced"** and add these environment variables:

**Required Variables:**

```
CLAUDE_API_KEY = your_claude_api_key_here
PORT = 5001
```

**Optional Variables:**

```
GITHUB_TOKEN = your_github_token_here
SKIP_API_CALL = true
POLICY_FILE = data/v5 Freya POL-11 Access Control.docx
OUTPUT_NAME = policy_tracked_changes_with_comments
# NOTE: QUESTIONNAIRE_FILE removed - system now uses localStorage data only
```

**How to add each variable:**

1. Click **"Add Environment Variable"**
2. Enter **Key** (e.g., `CLAUDE_API_KEY`)
3. Enter **Value** (your actual API key)
4. Click **"Add"**
5. Repeat for each variable

### Step 6: Deploy

1. **Click "Create Web Service"**
2. **Wait for deployment** (usually 2-5 minutes)
3. **Watch the build logs** in real-time

**You'll see logs like:**

```
Building...
Installing dependencies...
Starting web service...
Your service is live at https://policy-configurator-api.onrender.com
```

### Step 7: Test Your Deployment

1. **Copy your Render URL** (e.g., `https://policy-configurator-api.onrender.com`)

2. **Test the API endpoints**:

   ```bash
   # Test health check
   curl https://your-app.onrender.com/

   # Test status endpoint
   curl https://your-app.onrender.com/api/status
   ```

3. **Expected response from `/api/status`**:
   ```json
   {
     "api_key_configured": true,
     "automation_running": false,
     "policy_exists": true,
     "policy_file": "data/v5 Freya POL-11 Access Control.docx",
     "questionnaire_exists": true,
     "questionnaire_file": "data/secfix_questionnaire_responses_consulting.csv",
     "skip_api": true
   }
   ```

## 🔧 Configuration Details

### Important Render Settings

**Auto-Deploy:**

- ✅ Enabled by default
- Automatically deploys when you push to GitHub
- Can be disabled in Settings if needed

**Health Checks:**

- Render automatically monitors your service
- Restarts if it becomes unresponsive
- Shows status on dashboard

**Logs:**

- Available in real-time on Render dashboard
- Useful for debugging issues
- Retained for 7 days on free tier

## 🐛 Troubleshooting

### Common Issues:

**1. Build Fails - "No such file or directory"**

```
Solution: Ensure Root Directory is set to "web_ui"
```

**2. Service Starts but API Returns 404**

```
Check: Start Command should be "python3 app.py"
Check: PORT environment variable is set to 5001
```

**3. Import Errors**

```
Check: All dependencies in requirements.txt
Check: File paths are relative to web_ui directory
```

**4. Environment Variables Not Working**

```
Check: Variables are set in Render dashboard
Check: No extra spaces in variable names/values
Check: Restart service after adding variables
```

**5. Service Sleeps/Slow Response**

```
Note: Free tier services sleep after 15 minutes of inactivity
Solution: First request after sleep takes 10-30 seconds
Upgrade: Paid plans don't sleep
```

### Debugging Steps:

1. **Check Build Logs:**

   - Go to Render dashboard
   - Click on your service
   - Check "Events" tab for build errors

2. **Check Runtime Logs:**

   - Go to "Logs" tab
   - Look for Python errors or startup issues

3. **Test Locally:**
   ```bash
   cd web_ui
   pip install -r requirements.txt
   python3 app.py
   ```

## 📋 Post-Deployment Checklist

- [ ] Service builds successfully
- [ ] API responds at your Render URL
- [ ] `/api/status` returns correct data
- [ ] Environment variables loaded correctly
- [ ] CORS headers present in responses
- [ ] No errors in Render logs

## 🔗 Next Steps

After successful deployment:

1. **Copy your Render URL** (e.g., `https://policy-configurator-api.onrender.com`)

2. **Deploy Next.js frontend** using this URL:

   ```bash
   ./deploy.sh https://policy-configurator-api.onrender.com
   ```

3. **Test the complete system** with frontend + backend

## 💡 Pro Tips

**Free Tier Optimization:**

- Services sleep after 15 minutes of inactivity
- Consider a paid plan ($7/month) for always-on services
- Use cron jobs to ping your service to keep it awake

**Security:**

- Never commit API keys to Git
- Use Render's environment variables for secrets
- Consider restricting CORS origins in production

**Monitoring:**

- Enable email notifications for service failures
- Check logs regularly during initial deployment
- Monitor response times in Render dashboard

**Scaling:**

- Start with free tier for testing
- Upgrade to paid tier for production use
- Consider multiple regions for global users

## 🎯 Success Indicators

✅ **Your deployment is successful when:**

- Build completes without errors
- Service status shows "Live"
- API endpoints return expected data
- No errors in logs
- Response time is reasonable (<2 seconds)

Your Flask API will be available at: `https://your-service-name.onrender.com`
