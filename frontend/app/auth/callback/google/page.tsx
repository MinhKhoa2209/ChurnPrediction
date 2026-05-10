'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuthStore } from '@/lib/store/auth-store';
import { announceToScreenReader } from '@/lib/accessibility';

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get token or error from URL parameters
        const token = searchParams.get('token');
        const errorParam = searchParams.get('error');
        const code = searchParams.get('code');

        if (errorParam) {
          let errorMessage = 'Google sign in failed';
          switch (errorParam) {
            case 'provider_not_configured':
              errorMessage = 'OAuth provider is not configured. Please contact administrator.';
              break;
            case 'no_email':
              errorMessage = 'Email not provided by Google. Please try again.';
              break;
            case 'auth_failed':
              errorMessage = 'Authentication failed. Please try again.';
              break;
            default:
              errorMessage = `OAuth error: ${errorParam}`;
          }
          throw new Error(errorMessage);
        }

        if (code && !token) {
          const queryString = searchParams.toString();
          const callbackUrl = queryString
            ? `/api/v1/oauth/google/callback?${queryString}`
            : '/api/v1/oauth/google/callback';
          window.location.replace(callbackUrl);
          return;
        }

        if (!token) {
          throw new Error('No authentication token received');
        }

        // Fetch user info using the token
        const response = await fetch('/api/v1/auth/me', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for CORS
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Failed to fetch user info:', errorText);
          throw new Error('Failed to fetch user information');
        }

        const userData = await response.json();

        // Ensure all required User fields are present
        const user = {
          id: userData.id,
          email: userData.email,
          role: userData.role,
          name: userData.name || null,
          avatar: userData.avatar || null,
          provider: userData.provider || 'google',
          created_at: userData.created_at,
          email_verified: userData.email_verified ?? true,
          email_notifications_enabled: userData.email_notifications_enabled ?? true,
        };

        // Store auth data
        setAuth(user, token);

        // Success
        announceToScreenReader('Google sign in successful. Redirecting to dashboard.', 'polite');
        toast.success('Welcome!', { description: 'You have signed in successfully with Google.' });

        // Redirect to dashboard
        router.push('/dashboard');

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Google sign in failed';
        setError(errorMessage);
        announceToScreenReader(`Google sign in failed: ${errorMessage}`, 'assertive');
        toast.error('Sign in failed', { description: errorMessage });

        // Redirect back to login after 3 seconds
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, router, setAuth]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-6 py-4 text-destructive max-w-md">
            <h2 className="font-semibold mb-2">Authentication Failed</h2>
            <p className="text-sm">{error}</p>
          </div>
          <p className="text-sm text-muted-foreground">Redirecting to login page...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
        <div>
          <h2 className="text-lg font-semibold">Completing sign in...</h2>
          <p className="text-sm text-muted-foreground">Please wait while we authenticate your account</p>
        </div>
      </div>
    </div>
  );
}
