# Vercel Setup Script for Customer Churn Prediction Platform (PowerShell)
# This script helps configure Vercel deployment for the frontend

$ErrorActionPreference = "Stop"

Write-Host "🚀 Vercel Deployment Setup Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if Vercel CLI is installed
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
if (-not $vercelInstalled) {
    Write-Host "Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
    Write-Host "✓ Vercel CLI installed" -ForegroundColor Green
} else {
    Write-Host "✓ Vercel CLI already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Prerequisites Checklist:" -ForegroundColor Cyan
Write-Host "1. Vercel account created at https://vercel.com"
Write-Host "2. GitHub repository connected to Vercel"
Write-Host "3. Backend deployed to Railway (for API URL)"
Write-Host ""

$continue = Read-Host "Have you completed all prerequisites? (y/n)"
if ($continue -ne "y" -and $continue -ne "Y") {
    Write-Host "Please complete prerequisites before continuing" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔐 Login to Vercel" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
vercel login

Write-Host ""
Write-Host "📦 Project Setup" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan
Write-Host "This will link your local project to Vercel"
Write-Host ""

# Navigate to frontend directory if not already there
if (-not (Test-Path "package.json")) {
    Set-Location frontend
}

# Link project to Vercel
vercel link

Write-Host ""
Write-Host "🌍 Environment Variables Setup" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You need to configure the following environment variables in Vercel:"
Write-Host ""
Write-Host "Required Variables:"
Write-Host "  - NEXT_PUBLIC_API_URL (Your Railway backend URL)"
Write-Host "  - NEXT_PUBLIC_WS_URL (Your Railway WebSocket URL)"
Write-Host "  - NEXT_PUBLIC_APP_ENV (production)"
Write-Host ""
Write-Host "Optional Variables:"
Write-Host "  - SENTRY_DSN (Error tracking)"
Write-Host "  - SENTRY_AUTH_TOKEN (Sentry authentication)"
Write-Host "  - NEXT_PUBLIC_ANALYTICS_ID (Analytics)"
Write-Host ""

$backendUrl = Read-Host "Enter your Railway backend URL (e.g., https://backend.railway.app)"
$wsUrl = Read-Host "Enter your Railway WebSocket URL (e.g., wss://backend.railway.app)"

if ($backendUrl) {
    Write-Host "Setting NEXT_PUBLIC_API_URL..." -ForegroundColor Yellow
    echo $backendUrl | vercel env add NEXT_PUBLIC_API_URL production
    echo $backendUrl | vercel env add NEXT_PUBLIC_API_URL preview
}

if ($wsUrl) {
    Write-Host "Setting NEXT_PUBLIC_WS_URL..." -ForegroundColor Yellow
    echo $wsUrl | vercel env add NEXT_PUBLIC_WS_URL production
    echo $wsUrl | vercel env add NEXT_PUBLIC_WS_URL preview
}

Write-Host "Setting NEXT_PUBLIC_APP_ENV..." -ForegroundColor Yellow
echo "production" | vercel env add NEXT_PUBLIC_APP_ENV production
echo "preview" | vercel env add NEXT_PUBLIC_APP_ENV preview

Write-Host ""
$configureSentry = Read-Host "Do you want to configure Sentry for error tracking? (y/n)"
if ($configureSentry -eq "y" -or $configureSentry -eq "Y") {
    $sentryDsn = Read-Host "Enter your Sentry DSN"
    $sentryToken = Read-Host "Enter your Sentry Auth Token"
    
    if ($sentryDsn) {
        echo $sentryDsn | vercel env add SENTRY_DSN production
        echo $sentryDsn | vercel env add SENTRY_DSN preview
    }
    
    if ($sentryToken) {
        echo $sentryToken | vercel env add SENTRY_AUTH_TOKEN production
    }
}

Write-Host ""
Write-Host "🏗️  Build Configuration" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Vercel will automatically detect Next.js and use the following:"
Write-Host "  - Framework: Next.js"
Write-Host "  - Build Command: npm run build"
Write-Host "  - Output Directory: .next"
Write-Host "  - Install Command: npm install"
Write-Host ""

Write-Host ""
Write-Host "🚀 Deployment" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
$deploy = Read-Host "Do you want to deploy now? (y/n)"
if ($deploy -eq "y" -or $deploy -eq "Y") {
    Write-Host "Deploying to preview environment..." -ForegroundColor Yellow
    vercel
    
    Write-Host ""
    $deployProd = Read-Host "Deploy to production? (y/n)"
    if ($deployProd -eq "y" -or $deployProd -eq "Y") {
        Write-Host "Deploying to production..." -ForegroundColor Yellow
        vercel --prod
    }
}

Write-Host ""
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Configure custom domain in Vercel dashboard (optional)"
Write-Host "2. Set up GitHub Actions secrets for CI/CD:"
Write-Host "   - VERCEL_TOKEN"
Write-Host "   - VERCEL_ORG_ID"
Write-Host "   - VERCEL_PROJECT_ID"
Write-Host "3. Enable Vercel Analytics in project settings"
Write-Host "4. Configure deployment protection (optional)"
Write-Host ""
Write-Host "Documentation: See VERCEL_DEPLOYMENT.md for detailed instructions"
Write-Host ""
Write-Host "🎉 Your frontend is ready for deployment!" -ForegroundColor Green
