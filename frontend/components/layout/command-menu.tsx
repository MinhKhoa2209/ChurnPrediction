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
} from 'lucide-react';
import { useAuthStore } from '@/lib/store/auth-store';

interface CommandItem {
  label: string;
  href: string;
  icon: React.ElementType;
  shortcut?: string;
  roles?: string[];
}

const commandItems: CommandItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, shortcut: '⌘D', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Getting Started', href: '/getting-started', icon: Rocket, roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Upload Data', href: '/data/upload', icon: Upload, shortcut: '⌘U', roles: ['Admin', 'Data_Scientist'] },
  { label: 'Models', href: '/models', icon: BrainCircuit, roles: ['Admin', 'Data_Scientist'] },
  { label: 'Predictions', href: '/predictions', icon: Sparkles, shortcut: '⌘P', roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Reports', href: '/reports', icon: FileBarChart2, roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Notifications', href: '/notifications', icon: Bell, roles: ['Admin', 'Data_Scientist', 'Analyst'] },
  { label: 'Settings', href: '/settings', icon: Settings, roles: ['Admin', 'Data_Scientist', 'Analyst'] },
];

export function CommandMenu() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { user } = useAuthStore();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const visible = commandItems.filter(
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
          {visible.map((item) => {
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
          <CommandItem onSelect={() => handleSelect('/data/upload')}>
            <Upload className="mr-2 h-4 w-4" />
            Upload new dataset
          </CommandItem>
          <CommandItem onSelect={() => handleSelect('/predictions/single')}>
            <Sparkles className="mr-2 h-4 w-4" />
            Make a prediction
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
