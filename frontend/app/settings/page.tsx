'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store/auth-store';
import { useTheme } from 'next-themes';
import { API_BASE_URL } from '@/lib/api';

export default function SettingsPage() {
  const { user, token } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (user) {
      queueMicrotask(() => {
        setEmailNotifications(user.email_notifications_enabled || false);
      });
    }
  }, [user]);

  const handleSaveNotifications = async () => {
    if (!token) return;

    setIsLoading(true);
    setSaveMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/settings`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          email_notifications_enabled: emailNotifications,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save notification preferences');
      }

      setSaveMessage({ type: 'success', text: 'Notification preferences saved successfully' });
      
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Error saving notification preferences:', error);
      setSaveMessage({ type: 'error', text: 'Failed to save notification preferences' });
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8 text-foreground">Settings</h1>

      <section 
        className="bg-card rounded-lg shadow p-6 mb-6"
        aria-labelledby="profile-heading"
      >
        <h2 id="profile-heading" className="text-xl font-semibold mb-4 text-foreground">
          Profile
        </h2>
        <div className="space-y-4">
          <div>
            <label 
              htmlFor="email" 
              className="block text-sm font-medium mb-2 text-muted-foreground"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={user.email}
              disabled
              className="w-full px-3 py-2 border border-border rounded-lg bg-muted text-muted-foreground cursor-not-allowed"
              aria-describedby="email-description"
            />
            <p id="email-description" className="mt-1 text-xs text-muted-foreground">
              Email cannot be changed
            </p>
          </div>
          <div>
            <label 
              htmlFor="role" 
              className="block text-sm font-medium mb-2 text-muted-foreground"
            >
              Role
            </label>
            <input
              id="role"
              type="text"
              value={user.role}
              disabled
              className="w-full px-3 py-2 border border-border rounded-lg bg-muted text-muted-foreground cursor-not-allowed"
              aria-describedby="role-description"
            />
            <p id="role-description" className="mt-1 text-xs text-muted-foreground">
              Role is assigned by administrators
            </p>
          </div>
        </div>
      </section>

      <section 
        className="bg-card rounded-lg shadow p-6 mb-6"
        aria-labelledby="appearance-heading"
      >
        <h2 id="appearance-heading" className="text-xl font-semibold mb-4 text-foreground">
          Appearance
        </h2>
        <div>
          <label 
            htmlFor="theme" 
            className="block text-sm font-medium mb-2 text-muted-foreground"
          >
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
            className="w-full px-3 py-2 border border-border rounded-lg bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            aria-describedby="theme-description"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
          </select>
          <p id="theme-description" className="mt-1 text-xs text-muted-foreground">
            Choose your preferred color theme. System will match your device settings.
          </p>
        </div>
      </section>

      <section 
        className="bg-card rounded-lg shadow p-6"
        aria-labelledby="notifications-heading"
      >
        <h2 id="notifications-heading" className="text-xl font-semibold mb-4 text-foreground">
          Notifications
        </h2>
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="email-notifications"
                type="checkbox"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="w-4 h-4 text-primary bg-input border-border rounded focus:ring-ring focus:ring-2"
                aria-describedby="email-notifications-description"
              />
            </div>
            <div className="ml-3">
              <label 
                htmlFor="email-notifications" 
                className="text-sm font-medium text-foreground cursor-pointer"
              >
                Email notifications
              </label>
              <p id="email-notifications-description" className="text-xs text-muted-foreground">
                Receive email notifications when training jobs complete or fail
              </p>
            </div>
          </div>

          {saveMessage && (
            <div
              className={`p-3 rounded-lg ${
                saveMessage.type === 'success'
                  ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                  : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
              }`}
              role="alert"
              aria-live="polite"
            >
              {saveMessage.text}
            </div>
          )}

          <button
            onClick={handleSaveNotifications}
            disabled={isLoading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Save notification preferences"
          >
            {isLoading ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </section>
    </div>
  );
}
