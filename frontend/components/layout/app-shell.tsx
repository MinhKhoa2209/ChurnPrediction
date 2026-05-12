'use client';

import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { AppSidebar } from './app-sidebar';
import { AppHeader } from './app-header';
import { CommandMenu } from './command-menu';
import { useAuthStore } from '@/lib/store/auth-store';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user } = useAuthStore();

  // Don't render the app shell for unauthenticated users
  if (!user) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <AppHeader />
        <main
          id="main-content"
          className="flex min-w-0 flex-1 flex-col gap-4 overflow-x-hidden p-4 pt-4 md:p-6"
        >
          {children}
        </main>
      </SidebarInset>
      <CommandMenu />
    </SidebarProvider>
  );
}
