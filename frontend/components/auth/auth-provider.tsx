'use client';

/**
 * Authentication Provider Component
 * Handles authentication state initialization and validation
 */

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { getCurrentUser } from '@/lib/auth';

const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, setAuth, clearAuth, setLoading } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  // Wait for Zustand store to rehydrate from localStorage
  useEffect(() => {
    // Mark as hydrated after first render (store has rehydrated by then)
    setHydrated(true);
  }, []);

  useEffect(() => {
    // Don't validate until store has hydrated
    if (!hydrated) {
      return;
    }

    const validateAuth = async () => {
      // Skip validation for public routes
      if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
        setLoading(false);
        return;
      }

      // If no token, redirect to login
      if (!token) {
        // Requirement 1.6: Redirect unauthenticated users to login page
        setLoading(false);
        router.push('/login');
        return;
      }

      try {
        // Requirement 1.7: Validate session token
        const user = await getCurrentUser(token);
        setAuth(user, token);
      } catch (error) {
        // Token is invalid or expired, clear auth and redirect
        console.error('Token validation failed:', error);
        clearAuth();
        router.push('/login');
      }
    };

    validateAuth();
  }, [hydrated, pathname, token, router, setAuth, clearAuth, setLoading]);

  // Show loading state while hydrating
  if (!hydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-gray-900 dark:text-white" role="status" aria-live="polite">
          Loading...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
