'use client';


import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { getCurrentUser } from '@/lib/auth';

const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password', '/admin/login'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, setAuth, clearAuth, setLoading } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    const validateAuth = async () => {
      if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
        setLoading(false);
        return;
      }

      if (!token) {
        setLoading(false);
        router.push('/login');
        return;
      }

      try {
        const user = await getCurrentUser(token);
        setAuth(user, token);
      } catch (error) {
        console.error('Token validation failed:', error);
        clearAuth();
        router.push('/login');
      }
    };

    validateAuth();
  }, [hydrated, pathname, token, router, setAuth, clearAuth, setLoading]);

  if (!hydrated) {
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
