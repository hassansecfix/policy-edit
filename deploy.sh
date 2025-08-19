#!/bin/bash

# Policy Automation - Deployment Script
# This script helps deploy the Next.js frontend to Vercel

echo "🚀 Policy Automation Deployment Helper"
echo "======================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -d "web_app" ]; then
    echo -e "${RED}❌ Error: Run this script from the policy-edit project root${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Pre-deployment checklist:${NC}"
echo "1. ✅ Flask backend deployed and URL obtained"
echo "2. ✅ Vercel account created"
echo "3. ✅ GitHub repository pushed"
echo ""

# Check if API URL is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}⚠️  Please provide your deployed Flask API URL:${NC}"
    echo -e "${BLUE}Usage: ./deploy.sh https://your-flask-api.onrender.com${NC}"
    echo ""
    echo -e "${BLUE}💡 Deploy your Flask backend first, then run:${NC}"
    echo -e "${BLUE}   ./deploy.sh https://your-api-url-here${NC}"
    exit 1
fi

API_URL="$1"
echo -e "${GREEN}🔗 Using API URL: ${API_URL}${NC}"

# Navigate to web_app directory
cd web_app

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Vercel CLI...${NC}"
    npm install -g vercel
fi

# Build the project locally to check for errors
echo -e "${BLUE}🔨 Building project locally...${NC}"
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed! Please fix errors before deploying.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful!${NC}"

# Deploy to Vercel
echo -e "${BLUE}🚀 Deploying to Vercel...${NC}"

# Set environment variable and deploy
vercel --prod --env NEXT_PUBLIC_API_URL="$API_URL"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo -e "${BLUE}📝 Next steps:${NC}"
    echo "1. Test your deployed app"
    echo "2. Check browser console for any errors"
    echo "3. Verify API connection is working"
    echo "4. Test file downloads"
    echo ""
    echo -e "${YELLOW}💡 Your app should be available at the URL shown above${NC}"
else
    echo -e "${RED}❌ Deployment failed! Check the error messages above.${NC}"
    exit 1
fi
