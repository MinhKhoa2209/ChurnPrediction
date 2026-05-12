'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { listUsers } from '@/lib/users';
import type { User } from '@/lib/auth';
import { User as UserIcon, Shield, ShieldAlert, Search, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function UsersManagementPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // State removed

  const fetchUsers = useCallback(async () => {
    try {
      setError(null);
      const data = await listUsers(token!);
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!token || !user) {
      router.push('/login');
      return;
    }

    if (user.role !== 'Admin') {
      router.push('/dashboard');
      return;
    }

    queueMicrotask(() => {
      void fetchUsers();
    });
  }, [user, token, authLoading, router, fetchUsers]);

  // handleDeleteUser removed

  // Client-side search: name, email, role — case-insensitive
  const filteredUsers = useMemo(() => {
    let result = users;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = users.filter(u =>
        (u.name && u.name.toLowerCase().includes(q)) ||
        u.email.toLowerCase().includes(q) ||
        u.role.toLowerCase().includes(q)
      );
    }
    
    // Sort so the current user is at the top
    if (user?.id) {
      result = [...result].sort((a, b) => {
        if (a.id === user.id) return -1;
        if (b.id === user.id) return 1;
        return 0;
      });
    }
    
    return result;
  }, [users, searchQuery, user?.id]);

  if (authLoading || (user?.role === 'Admin' && isLoading)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (user.role !== 'Admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Redirecting to the dashboard...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Users Management
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          <div className="bg-white dark:bg-card shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-foreground">
                  System Users
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
                  View and manage user accounts.
                </p>
              </div>
              <div className="flex items-center gap-4">
                {/* Search input */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by name, email, or role..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-background text-gray-900 dark:text-foreground placeholder-gray-400 dark:placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64"
                    id="user-search-input"
                  />
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  {filteredUsers.length} of {users.length} users
                </div>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
                <thead className="bg-gray-50 dark:bg-muted">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      User
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Role
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Created At
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-card divide-y divide-gray-200 dark:divide-border">
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                            <UserIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-foreground">
                              {u.name || 'No Name'}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {u.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          u.role === 'Admin' 
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' 
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                        }`}>
                          {u.role === 'Admin' ? <ShieldAlert className="w-3 h-3 mr-1" /> : <Shield className="w-3 h-3 mr-1" />}
                          {u.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(u.created_at).toLocaleDateString()}
                        {u.id === user.id && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">
                            Current User
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredUsers.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-500 dark:text-gray-400">
                    {searchQuery ? 'No users match your search.' : 'No users found.'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Delete Confirmation Modal removed */}
    </div>
  );
}
