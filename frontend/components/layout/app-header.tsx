'use client';

import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Breadcrumbs } from './breadcrumbs';
import { ThemeToggle } from './theme-toggle';
import { Badge } from '@/components/ui/badge';
import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store/auth-store';
import { getUnreadCount } from '@/lib/notifications';

export function AppHeader() {
  const { token } = useAuthStore();
  const [unreadCount, setUnreadCount] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!token) return;

    const fetchCount = async () => {
      try {
        const count = await getUnreadCount(token);
        setUnreadCount(count);
      } catch {
        // Silently fail — bell just won't show count
      }
    };

    // Fetch immediately
    fetchCount();

    // Poll every 30 seconds
    intervalRef.current = setInterval(fetchCount, 30000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [token]);

  return (
    <header className="sticky inset-x-0 top-0 z-50 flex h-14 w-full min-w-0 shrink-0 items-center gap-2 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />
      <Breadcrumbs />

      <div className="ml-auto flex items-center gap-2">
        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 relative"
          asChild
          aria-label={unreadCount > 0 ? `${unreadCount} unread notifications` : 'Notifications'}
        >
          <Link href="/notifications">
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-0.5 -right-0.5 h-4 min-w-4 p-0 text-[10px] flex items-center justify-center"
                aria-label={`${unreadCount} new notifications`}
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </Badge>
            )}
          </Link>
        </Button>

        <ThemeToggle />
      </div>
    </header>
  );
}
