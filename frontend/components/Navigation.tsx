'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { logout as logoutApi } from '@/lib/auth';
import { trapFocus, announceToScreenReader } from '@/lib/accessibility';
import { ThemeToggle } from '@/components/ThemeToggle';
import { getUnreadCount } from '@/lib/notifications';
import { Menu, X } from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon?: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', roles: ['Admin', 'Analyst'] },
  { label: 'Getting Started', href: '/getting-started', roles: ['Admin', 'Analyst'] },
  { label: 'Data Upload', href: '/data/upload', roles: ['Admin'] },
  { label: 'Data Processing', href: '/data/processing', roles: ['Admin'] },
  { label: 'Models', href: '/models', roles: ['Admin', 'Analyst'] },
  { label: 'Predictions', href: '/predictions', roles: ['Admin', 'Analyst'] },
  { label: 'Reports', href: '/reports', roles: ['Admin', 'Analyst'] },
  { label: 'Notifications', href: '/notifications', roles: ['Admin', 'Analyst'] },
  { label: 'Users', href: '/admin/users', roles: ['Admin'] },
  { label: 'Settings', href: '/settings', roles: ['Admin', 'Analyst'] },
];

export function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, token, clearAuth } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  const visibleNavItems = navItems.filter(
    (item) => !item.roles || (user?.role && item.roles.includes(user.role))
  );

  // Fetch unread notification count
  useEffect(() => {
    const fetchUnreadCount = async () => {
      if (token) {
        try {
          const count = await getUnreadCount(token);
          setUnreadCount(count);
        } catch (error) {
          console.error('Error fetching unread count:', error);
        }
      }
    };

    fetchUnreadCount();
    
    // Poll every 30 seconds for new notifications
    const interval = setInterval(fetchUnreadCount, 30000);
    
    return () => clearInterval(interval);
  }, [token]);

  // Refresh unread count when pathname changes (e.g., after marking as read)
  useEffect(() => {
    if (token && pathname === '/notifications') {
      const fetchUnreadCount = async () => {
        try {
          const count = await getUnreadCount(token);
          setUnreadCount(count);
        } catch (error) {
          console.error('Error fetching unread count:', error);
        }
      };
      fetchUnreadCount();
    }
  }, [pathname, token]);

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
              const isNotifications = item.href === '/notifications';
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isActive
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {item.label}
                  {isNotifications && unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full">
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
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
                <X className="h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="h-6 w-6" aria-hidden="true" />
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
              const isNotifications = item.href === '/notifications';
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`relative flex items-center justify-between px-3 py-2 rounded-md text-base font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isActive
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <span>{item.label}</span>
                  {isNotifications && unreadCount > 0 && (
                    <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full">
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
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
