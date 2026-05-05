import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth/auth-provider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ToastProvider } from "@/components/ToastProvider";
import { DegradedModeProvider } from "@/components/DegradedModeProvider";
import { ScreenReaderAnnouncer } from "@/components/ScreenReaderAnnouncer";
import { ThemeProvider } from "@/lib/theme-provider";
import { SpeedInsights } from '@vercel/speed-insights/next';
import { Analytics } from '@vercel/analytics/react';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Customer Churn Prediction Platform",
  description: "ML-powered customer churn prediction and analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        {/* Skip link for keyboard navigation - Requirement 28.2 */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Skip to main content
        </a>
        
        <ThemeProvider>
          <ErrorBoundary>
            <AuthProvider>
              <DegradedModeProvider>
                <main id="main-content" className="flex-1">
                  {children}
                </main>
              </DegradedModeProvider>
            </AuthProvider>
            <ToastProvider />
            <ScreenReaderAnnouncer />
          </ErrorBoundary>
        </ThemeProvider>
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}
