'use client';

import { useState } from 'react';
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
  const [commandOpen, setCommandOpen] = useState(false);

  // Don't render the app shell for unauthenticated users
  if (!user) {
    return <>{children}</>;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <AppHeader onCommandMenuOpen={() => setCommandOpen(true)} />
        <main
          id="main-content"
          className="flex flex-1 flex-col gap-4 p-4 md:p-6 pt-4"
        >
          {children}
        </main>
      </SidebarInset>
      <CommandMenu />
    </SidebarProvider>
  );
}
