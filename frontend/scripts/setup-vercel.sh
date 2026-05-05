#!/bin/bash

# Vercel Setup Script for Customer Churn Prediction Platform
# This script helps configure Vercel deployment for the frontend

set -e

echo "🚀 Vercel Deployment Setup Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
    echo -e "${GREEN}✓ Vercel CLI installed${NC}"
else
    echo -e "${GREEN}✓ Vercel CLI already installed${NC}"
fi

echo ""
echo "📋 Prerequisites Checklist:"
echo "1. Vercel account created at https://vercel.com"
echo "2. GitHub repository connected to Vercel"
echo "3. Backend deployed to Railway (for API URL)"
echo ""

read -p "Have you completed all prerequisites? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Please complete prerequisites before continuing${NC}"
    exit 1
fi

echo ""
echo "🔐 Login to Vercel"
echo "=================="
vercel login

echo ""
echo "📦 Project Setup"
echo "================"
echo "This will link your local project to Vercel"
echo ""

# Navigate to frontend directory if not already there
if [ ! -f "package.json" ]; then
    cd frontend
fi

# Link project to Vercel
vercel link

echo ""
echo "🌍 Environment Variables Setup"
echo "=============================="
echo ""
echo "You need to configure the following environment variables in Vercel:"
echo ""
echo "Required Variables:"
echo "  - NEXT_PUBLIC_API_URL (Your Railway backend URL)"
echo "  - NEXT_PUBLIC_WS_URL (Your Railway WebSocket URL)"
echo "  - NEXT_PUBLIC_APP_ENV (production)"
echo ""
echo "Optional Variables:"
echo "  - SENTRY_DSN (Error tracking)"
echo "  - SENTRY_AUTH_TOKEN (Sentry authentication)"
echo "  - NEXT_PUBLIC_ANALYTICS_ID (Analytics)"
echo ""

read -p "Enter your Railway backend URL (e.g., https://backend.railway.app): " BACKEND_URL
read -p "Enter your Railway WebSocket URL (e.g., wss://backend.railway.app): " WS_URL

if [ -n "$BACKEND_URL" ]; then
    echo "Setting NEXT_PUBLIC_API_URL..."
    vercel env add NEXT_PUBLIC_API_URL production <<< "$BACKEND_URL"
    vercel env add NEXT_PUBLIC_API_URL preview <<< "$BACKEND_URL"
fi

if [ -n "$WS_URL" ]; then
    echo "Setting NEXT_PUBLIC_WS_URL..."
    vercel env add NEXT_PUBLIC_WS_URL production <<< "$WS_URL"
    vercel env add NEXT_PUBLIC_WS_URL preview <<< "$WS_URL"
fi

echo "Setting NEXT_PUBLIC_APP_ENV..."
vercel env add NEXT_PUBLIC_APP_ENV production <<< "production"
vercel env add NEXT_PUBLIC_APP_ENV preview <<< "preview"

echo ""
read -p "Do you want to configure Sentry for error tracking? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Sentry DSN: " SENTRY_DSN
    read -p "Enter your Sentry Auth Token: " SENTRY_AUTH_TOKEN
    
    if [ -n "$SENTRY_DSN" ]; then
        vercel env add SENTRY_DSN production <<< "$SENTRY_DSN"
        vercel env add SENTRY_DSN preview <<< "$SENTRY_DSN"
    fi
    
    if [ -n "$SENTRY_AUTH_TOKEN" ]; then
        vercel env add SENTRY_AUTH_TOKEN production <<< "$SENTRY_AUTH_TOKEN"
    fi
fi

echo ""
echo "🏗️  Build Configuration"
echo "======================"
echo "Vercel will automatically detect Next.js and use the following:"
echo "  - Framework: Next.js"
echo "  - Build Command: npm run build"
echo "  - Output Directory: .next"
echo "  - Install Command: npm install"
echo ""

echo ""
echo "🚀 Deployment"
echo "============="
read -p "Do you want to deploy now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deploying to preview environment..."
    vercel
    
    echo ""
    read -p "Deploy to production? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deploying to production..."
        vercel --prod
    fi
fi

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "Next Steps:"
echo "1. Configure custom domain in Vercel dashboard (optional)"
echo "2. Set up GitHub Actions secrets for CI/CD:"
echo "   - VERCEL_TOKEN"
echo "   - VERCEL_ORG_ID"
echo "   - VERCEL_PROJECT_ID"
echo "3. Enable Vercel Analytics in project settings"
echo "4. Configure deployment protection (optional)"
echo ""
echo "Documentation: See VERCEL_DEPLOYMENT.md for detailed instructions"
echo ""
echo -e "${GREEN}🎉 Your frontend is ready for deployment!${NC}"
