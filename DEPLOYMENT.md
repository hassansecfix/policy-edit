# Deployment Guide

This guide covers deploying both the Flask API backend and Next.js frontend to production.

## Architecture Overview

- **Frontend**: Next.js app deployed to Vercel
- **Backend**: Flask API deployed to Render/Railway/Heroku
- **Communication**: Frontend connects to backend via environment variables

## 🚀 Deploy Flask Backend

### Option 1: Render (Recommended - Free Tier Available)

1. **Create account** at [render.com](https://render.com)

2. **Connect your repository** and create a new Web Service

3. **Configure the service:**

   ```
   Name: policy-automation-api
   Environment: Python 3
   Build Command: cd web_ui && pip install -r requirements.txt
   Start Command: cd web_ui && python3 app.py
   ```

4. **Set environment variables:**

   ```
   CLAUDE_API_KEY=your_claude_api_key_here
   GITHUB_TOKEN=your_github_token_here
   SKIP_API_CALL=true
   PORT=5001
   ```

5. **Deploy** - Render will provide you with a URL like `https://policy-automation-api.onrender.com`

### Option 2: Railway

1. **Create account** at [railway.app](https://railway.app)

2. **Deploy from GitHub** - connect your repository

3. **Configure:**

   ```
   Root Directory: web_ui
   Build Command: pip install -r requirements.txt
   Start Command: python3 app.py
   ```

4. **Set environment variables** (same as above)

### Option 3: Heroku

1. **Create account** at [heroku.com](https://heroku.com)

2. **Create Procfile** in `web_ui/` directory:

   ```
   web: python3 app.py
   ```

3. **Deploy using Heroku CLI** or GitHub integration

## ⚛️ Deploy Next.js Frontend to Vercel

### Step 1: Prepare for Deployment

1. **Create Vercel account** at [vercel.com](https://vercel.com)

2. **Install Vercel CLI** (optional):
   ```bash
   npm i -g vercel
   ```

### Step 2: Deploy to Vercel

**Option A: GitHub Integration (Recommended)**

1. **Push your code** to GitHub
2. **Import project** on Vercel dashboard
3. **Configure:**

   ```
   Framework Preset: Next.js
   Root Directory: web_app
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```

4. **Set environment variable:**

   ```
   NEXT_PUBLIC_API_URL = https://your-flask-api-url.onrender.com
   ```

5. **Deploy** - Vercel will provide you with a URL

**Option B: Vercel CLI**

1. **Navigate to web_app directory:**

   ```bash
   cd web_app
   ```

2. **Deploy:**

   ```bash
   vercel
   ```

3. **Set environment variable:**

   ```bash
   vercel env add NEXT_PUBLIC_API_URL
   # Enter your Flask API URL when prompted
   ```

4. **Redeploy** with environment variables:
   ```bash
   vercel --prod
   ```

## 🔧 Configuration

### Environment Variables

**Flask Backend (.env or deployment platform):**

```bash
CLAUDE_API_KEY=your_claude_api_key
GITHUB_TOKEN=your_github_token
SKIP_API_CALL=true
PORT=5001
```

**Next.js Frontend (Vercel):**

```bash
NEXT_PUBLIC_API_URL=https://your-flask-api.onrender.com
```

### CORS Configuration

The Flask backend is already configured to accept requests from any origin. For production, you may want to restrict this to your Vercel domain:

```python
# In web_ui/app.py
CORS(app, origins=["https://your-app.vercel.app"])
```

## 📋 Deployment Checklist

### Before Deploying:

- [ ] Flask API tested locally
- [ ] Next.js app tested locally
- [ ] Environment variables configured
- [ ] API endpoints working
- [ ] File downloads working

### After Deploying:

- [ ] Flask API accessible at deployment URL
- [ ] Next.js app loads correctly
- [ ] API connection working (check browser console)
- [ ] WebSocket connection working
- [ ] File downloads working from production

## 🐛 Troubleshooting

### Common Issues:

1. **CORS Errors**

   - Ensure Flask backend CORS is configured correctly
   - Check that API URL is correct in Next.js environment variables

2. **WebSocket Connection Fails**

   - Some deployment platforms may not support WebSockets
   - Consider upgrading to paid tier or switching platforms

3. **File Downloads Not Working**

   - Check file permissions in deployment environment
   - Ensure temporary file storage works on your platform

4. **API Timeout**
   - Increase timeout settings on your deployment platform
   - Consider upgrading to faster instance types

## 🎯 Success URLs

After successful deployment:

- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-api.onrender.com`
- **Test API**: `https://your-api.onrender.com/api/status`

## 💡 Tips

- Use **Render** for Flask backend (free tier available)
- Use **Vercel** for Next.js frontend (excellent Next.js support)
- Set up **GitHub Actions** for automated deployments
- Monitor **logs** in both platforms for debugging
- Consider **custom domains** for production use
