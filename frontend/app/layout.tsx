import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth/auth-provider";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { DegradedModeProvider } from "@/components/DegradedModeProvider";
import { ScreenReaderAnnouncer } from "@/components/ScreenReaderAnnouncer";
import { ThemeProvider } from "@/components/layout/theme-provider-wrapper";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppShell } from "@/components/layout";
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
  title: {
    default: "ChurnPredict — ML-Powered Customer Analytics",
    template: "%s | ChurnPredict",
  },
  description: "AI-powered customer churn prediction and analytics platform. Identify at-risk customers before they leave.",
  keywords: ["churn prediction", "machine learning", "customer analytics", "AI"],
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
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
        >
          Skip to main content
        </a>

        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <TooltipProvider delayDuration={200}>
            <ErrorBoundary>
              <AuthProvider>
                <DegradedModeProvider>
                  <AppShell>
                    {children}
                  </AppShell>
                </DegradedModeProvider>
              </AuthProvider>
              <ScreenReaderAnnouncer />
            </ErrorBoundary>
          </TooltipProvider>
          <Toaster position="top-right" richColors closeButton />
        </ThemeProvider>

        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}
