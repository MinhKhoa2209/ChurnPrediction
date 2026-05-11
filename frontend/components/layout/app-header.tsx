'use client';

import { Search, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Breadcrumbs } from './breadcrumbs';
import { ThemeToggle } from './theme-toggle';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '@/lib/store/auth-store';
import { getUnreadCount } from '@/lib/notifications';

interface AppHeaderProps {
  onCommandMenuOpen?: () => void;
}

export function AppHeader({ onCommandMenuOpen }: AppHeaderProps) {
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
    <header className="flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-40 px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />
      <Breadcrumbs />

      <div className="ml-auto flex items-center gap-2">
        {/* Search trigger */}
        <Button
          variant="outline"
          size="sm"
          className="hidden md:flex items-center gap-2 text-muted-foreground w-48 justify-start font-normal text-sm"
          onClick={onCommandMenuOpen}
          aria-label="Open command palette"
        >
          <Search className="h-3.5 w-3.5" />
          <span>Search...</span>
          <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100">
            <span className="text-xs">⌘</span>K
          </kbd>
        </Button>

        {/* Mobile search */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden h-8 w-8"
          onClick={onCommandMenuOpen}
          aria-label="Search"
        >
          <Search className="h-4 w-4" />
        </Button>

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
                className="absolute -top-0.5 -right-0.5 h-4 min-w-[1rem] p-0 text-[10px] flex items-center justify-center"
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
