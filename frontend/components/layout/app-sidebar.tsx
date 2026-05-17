'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Upload,
  BrainCircuit,
  Sparkles,
  FileBarChart2,
  Bell,
  Settings,
  Rocket,
  TrendingDown,
  ChevronRight,
  LogOut,
  User,
  Users,
  Activity,
} from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  useSidebar,
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuthStore } from '@/lib/store/auth-store';
import { logout as logoutApi } from '@/lib/auth';
import { announceToScreenReader } from '@/lib/accessibility';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  roles?: string[];
  badge?: string;
}

const mainNavItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['Admin', 'Analyst'] },
  { label: 'Getting Started', href: '/getting-started', icon: Rocket, roles: ['Admin', 'Analyst'] },
];

const dataNavItems: NavItem[] = [
  { label: 'Data Upload', href: '/data/upload', icon: Upload, roles: ['Admin'] },
  { label: 'Data Processing', href: '/data/processing', icon: Activity, roles: ['Admin'] },
  { label: 'Models', href: '/models/comparison', icon: BrainCircuit, roles: ['Admin', 'Analyst'] },
  { label: 'Predictions', href: '/predictions', icon: Sparkles, roles: ['Admin', 'Analyst'] },
  { label: 'Reports', href: '/reports', icon: FileBarChart2, roles: ['Admin', 'Analyst'] },
];

const settingsNavItems: NavItem[] = [
  { label: 'Notifications', href: '/notifications', icon: Bell, roles: ['Admin', 'Analyst'] },
  { label: 'Users', href: '/admin/users', icon: Users, roles: ['Admin'] },
  { label: 'Settings', href: '/settings', icon: Settings, roles: ['Admin', 'Analyst'] },
];

function NavGroup({ items, label }: { items: NavItem[]; label: string }) {
  const pathname = usePathname();
  const { user } = useAuthStore();

  const visible = items.filter(
    (item) => !item.roles || (user?.role && item.roles.includes(user.role))
  );

  if (!visible.length) return null;

  return (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarMenu>
        {visible.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;
          return (
            <SidebarMenuItem key={item.href}>
              <SidebarMenuButton
                asChild
                isActive={isActive}
                tooltip={item.label}
              >
                <Link href={item.href} aria-current={isActive ? 'page' : undefined}>
                  <Icon />
                  <span>{item.label}</span>
                  {item.badge && (
                    <Badge variant="secondary" className="ml-auto text-xs">
                      {item.badge}
                    </Badge>
                  )}
                  {isActive && <ChevronRight className="ml-auto h-3 w-3 opacity-50" />}
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}

export function AppSidebar() {
  const router = useRouter();
  const { user, token, clearAuth } = useAuthStore();
  const { isMobile } = useSidebar();

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

  const displayName = user?.name || user?.email || 'User';
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <Sidebar collapsible="icon" variant="sidebar">
      {/* Header / Brand */}
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/dashboard">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <TrendingDown className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold text-sm">ChurnPredict</span>
                  <span className="text-xs text-muted-foreground">ML Platform</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <NavGroup items={mainNavItems} label="Overview" />
        <SidebarSeparator />
        <NavGroup items={dataNavItems} label="Analytics" />
        <SidebarSeparator />
        <NavGroup items={settingsNavItems} label="System" />
      </SidebarContent>

      {/* User footer */}
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <Avatar className="h-8 w-8 rounded-lg">
                    {user?.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
                    <AvatarFallback className="rounded-lg bg-primary/10 text-primary text-xs font-semibold">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">{displayName}</span>
                    <span className="truncate text-xs text-muted-foreground">{user?.role}</span>
                  </div>
                  <ChevronRight className="ml-auto size-4" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-56 rounded-lg"
                side={isMobile ? 'bottom' : 'right'}
                align="end"
                sideOffset={4}
              >
                <DropdownMenuLabel className="p-0 font-normal">
                  <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                    <Avatar className="h-8 w-8 rounded-lg">
                      {user?.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
                      <AvatarFallback className="rounded-lg bg-primary/10 text-primary text-xs font-semibold">
                        {initials}
                      </AvatarFallback>
                    </Avatar>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-semibold">{displayName}</span>
                      <span className="truncate text-xs text-muted-foreground">{user?.email}</span>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/settings">
                    <User className="mr-2 h-4 w-4" />
                    Account Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={handleLogout}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
