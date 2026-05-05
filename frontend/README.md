# Customer Churn Prediction Platform - Frontend

Next.js 16 frontend application for the Customer Churn Prediction Platform.

## Technology Stack

- **Next.js 16** (App Router)
- **React 19**
- **TypeScript**
- **TailwindCSS v5**
- **shadcn/ui** (to be added)
- **Recharts** (to be added)
- **React Query** (to be added)
- **Zustand** (to be added)

## Setup

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
```

3. Update `.env.local` with your configuration

### Running the Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── dashboard/         # Dashboard pages
│   ├── data/              # Data upload and management
│   ├── eda/               # Exploratory data analysis
│   ├── models/            # Model training and evaluation
│   ├── predictions/       # Prediction interface
│   └── reports/           # Report generation
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── charts/           # Chart components
│   ├── forms/            # Form components
│   └── layout/           # Layout components
├── lib/                   # Utility libraries
│   ├── api.ts            # API client
│   ├── auth.ts           # Authentication utilities
│   └── utils.ts          # General utilities
├── hooks/                 # Custom React hooks
├── store/                 # Zustand state management
├── types/                 # TypeScript type definitions
└── public/                # Static assets
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_API_V1_PREFIX`: API version prefix (default: /api/v1)
- `NEXT_PUBLIC_WS_URL`: WebSocket URL for real-time updates

## Features

- 🎨 Modern UI with TailwindCSS v5 and shadcn/ui
- 📊 Interactive data visualizations with Recharts
- 🔐 Secure authentication with Better Auth
- 🌓 Dark mode support
- 📱 Responsive design (320px - 3840px)
- ♿ WCAG 2.1 Level AA accessibility
- 🚀 Optimized performance with Next.js 16
- 🔄 Real-time updates via WebSocket

## Requirements Coverage

This frontend implementation satisfies:
- Requirement 29.5: Frontend loads API endpoint URLs from environment variables
- Requirement 29.6: Example configuration files for different environments
- Requirement 28: Responsive design and accessibility (WCAG 2.1 Level AA)
- Requirement 2: Dashboard analytics display
- And many more UI/UX requirements

## Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Deployment

This application is configured for deployment on Vercel. Push to the main branch to trigger automatic deployment.

### Vercel Configuration

The project includes automatic configuration for Vercel deployment. Environment variables should be set in the Vercel dashboard.
