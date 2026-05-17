'use client';


import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { getCurrentUser } from '@/lib/auth';

const AUTH_ROUTES = ['/login', '/register', '/admin/login'];
const PUBLIC_ROUTES = [
  ...AUTH_ROUTES,
  '/forgot-password',
  '/reset-password',
  '/auth/callback',
];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, user, setAuth, clearAuth, setLoading } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));
  const isAuthRoute = AUTH_ROUTES.some(route => pathname.startsWith(route));

  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    const validateAuth = async () => {
      if (!token) {
        setLoading(false);
        if (!isPublicRoute) {
          router.push('/login');
        }
        return;
      }

      try {
        const currentUser = await getCurrentUser(token);
        setAuth(currentUser, token);
        if (isAuthRoute) {
          router.replace('/dashboard');
        }
      } catch (error) {
        console.error('Token validation failed:', error);
        clearAuth();
        if (!isPublicRoute) {
          router.push('/login');
        }
      }
    };

    validateAuth();
  }, [hydrated, isAuthRoute, isPublicRoute, pathname, token, router, setAuth, clearAuth, setLoading]);

  if (!hydrated || (isAuthRoute && (token || user))) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-foreground" role="status" aria-live="polite">
          Loading...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
