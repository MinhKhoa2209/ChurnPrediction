'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { logout as logoutApi } from '@/lib/auth';
import { trapFocus, announceToScreenReader } from '@/lib/accessibility';
import { ThemeToggle } from '@/components/ThemeToggle';

interface NavItem {
  label: string;
  href: string;
  icon?: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Getting Started', href: '/getting-started', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Data Upload', href: '/data/upload', roles: ['Admin', 'Data_Scientist'] },
  { label: 'Models', href: '/models', roles: ['Admin', 'Data_Scientist'] },
  { label: 'Predictions', href: '/predictions', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Reports', href: '/reports', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Notifications', href: '/notifications', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Settings', href: '/settings', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
];

export function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, token, clearAuth } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  const visibleNavItems = navItems.filter(
    (item) => !item.roles || (user?.role && item.roles.includes(user.role))
  );

  const toggleMobileMenu = () => {
    const newState = !isMobileMenuOpen;
    setIsMobileMenuOpen(newState);
    announceToScreenReader(
      newState ? 'Mobile menu opened' : 'Mobile menu closed',
      'polite'
    );
  };

  useEffect(() => {
    if (isMobileMenuOpen && mobileMenuRef.current) {
      const cleanup = trapFocus(mobileMenuRef.current);
      return cleanup;
    }
  }, [isMobileMenuOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
        announceToScreenReader('Mobile menu closed', 'polite');
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isMobileMenuOpen]);

  useEffect(() => {
    queueMicrotask(() => {
      setIsMobileMenuOpen(false);
    });
  }, [pathname]);

  const handleLogout = async () => {
    if (token) {
      try {
        await logoutApi(token);
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    clearAuth();
    router.push('/login');
    announceToScreenReader('You have been logged out', 'polite');
  };

  if (!user) {
    return null;
  }

  return (
    <nav
      className="bg-white dark:bg-card shadow-md"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link
              href="/dashboard"
              className="flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            >
              <span className="text-xl font-bold text-gray-900 dark:text-foreground">
                Churn Prediction
              </span>
            </Link>
          </div>

          <div className="hidden md:flex md:items-center md:space-x-4">
            {visibleNavItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isActive
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {item.label}
                </Link>
              );
            })}

            <div className="flex items-center space-x-4 ml-4 pl-4 border-l border-gray-200 dark:border-border">
              <ThemeToggle />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {user.email}
              </span>
              <button
                onClick={handleLogout}
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                aria-label="Log out"
              >
                Logout
              </button>
            </div>
          </div>

          <div className="flex items-center md:hidden">
            <button
              onClick={toggleMobileMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label="Toggle mobile menu"
            >
              <span className="sr-only">
                {isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              </span>
              {isMobileMenuOpen ? (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div
          ref={mobileMenuRef}
          id="mobile-menu"
          className="md:hidden border-t border-gray-200 dark:border-border"
        >
          <div className="px-2 pt-2 pb-3 space-y-1">
            {visibleNavItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block px-3 py-2 rounded-md text-base font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isActive
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>

          <div className="pt-4 pb-3 border-t border-gray-200 dark:border-border">
            <div className="px-4 mb-3 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-foreground">
                  {user.email}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {user.role}
                </div>
              </div>
              <ThemeToggle />
            </div>
            <button
              onClick={handleLogout}
              className="block w-full text-left px-4 py-2 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Log out"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
