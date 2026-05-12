'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command';
import {
  LayoutDashboard,
  Upload,
  BrainCircuit,
  Sparkles,
  FileBarChart2,
  Bell,
  Settings,
  Rocket,
  Users,
  Activity,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store/auth-store';

interface CommandMenuItem {
  label: string;
  href: string;
  icon: React.ElementType;
  shortcut?: string;
  roles?: string[];
}

const commandItems: CommandMenuItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, shortcut: '⌘D', roles: ['Admin', 'Analyst'] },
  { label: 'Getting Started', href: '/getting-started', icon: Rocket, roles: ['Admin', 'Analyst'] },
  { label: 'Upload Data', href: '/data/upload', icon: Upload, shortcut: '⌘U', roles: ['Admin'] },
  { label: 'Data Processing', href: '/data/processing', icon: Activity, roles: ['Admin'] },
  { label: 'Models', href: '/models', icon: BrainCircuit, roles: ['Admin', 'Analyst'] },
  { label: 'Predictions', href: '/predictions', icon: Sparkles, shortcut: '⌘P', roles: ['Admin', 'Analyst'] },
  { label: 'Reports', href: '/reports', icon: FileBarChart2, roles: ['Admin', 'Analyst'] },
  { label: 'Notifications', href: '/notifications', icon: Bell, roles: ['Admin', 'Analyst'] },
  { label: 'Users', href: '/admin/users', icon: Users, roles: ['Admin'] },
  { label: 'Settings', href: '/settings', icon: Settings, roles: ['Admin', 'Analyst'] },
];

interface CommandMenuProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function CommandMenu({ open: controlledOpen, onOpenChange }: CommandMenuProps = {}) {
  const [internalOpen, setInternalOpen] = useState(false);
  const router = useRouter();
  const { user } = useAuthStore();

  // Use controlled state if provided, otherwise use internal state
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(!open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [open, setOpen]);

  const visibleItems = commandItems.filter(
    (item) => !item.roles || (user?.role && item.roles.includes(user.role))
  );

  const handleSelect = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search pages, actions..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            return (
              <CommandItem
                key={item.href}
                value={item.label}
                onSelect={() => handleSelect(item.href)}
              >
                <Icon className="mr-2 h-4 w-4" />
                {item.label}
                {item.shortcut && (
                  <CommandShortcut>{item.shortcut}</CommandShortcut>
                )}
              </CommandItem>
            );
          })}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Quick Actions">
          {user?.role === 'Admin' && (
            <CommandItem onSelect={() => handleSelect('/data/upload')}>
              <Upload className="mr-2 h-4 w-4" />
              Upload new dataset
            </CommandItem>
          )}
          <CommandItem onSelect={() => handleSelect('/predictions')}>
            <Sparkles className="mr-2 h-4 w-4" />
            Make a prediction
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
