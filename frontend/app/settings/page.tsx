/**
 * User Settings Page
 * Provides user settings interface with:
 * - Profile information display (read-only)
 * - Theme selector (light/dark/system)
 * - Email notification preferences toggle
 * - Accessible form controls
 * - Responsive design
 */

'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth-store';
import { useTheme } from '@/lib/theme-provider';

interface NotificationSettings {
  emailNotificationsEnabled: boolean;
}

export default function SettingsPage() {
  const { user, token } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Initialize email notifications from user data
  useEffect(() => {
    if (user) {
      setEmailNotifications(user.email_notifications_enabled || false);
    }
  }, [user]);

  const handleSaveNotifications = async () => {
    if (!token) return;

    setIsLoading(true);
    setSaveMessage(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/settings`, {
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
      
      // Clear success message after 3 seconds
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
        <p className="text-gray-600 dark:text-gray-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8 text-gray-900 dark:text-white">Settings</h1>

      {/* Profile Settings */}
      <section 
        className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6"
        aria-labelledby="profile-heading"
      >
        <h2 id="profile-heading" className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Profile
        </h2>
        <div className="space-y-4">
          <div>
            <label 
              htmlFor="email" 
              className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={user.email}
              disabled
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
              aria-describedby="email-description"
            />
            <p id="email-description" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Email cannot be changed
            </p>
          </div>
          <div>
            <label 
              htmlFor="role" 
              className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300"
            >
              Role
            </label>
            <input
              id="role"
              type="text"
              value={user.role}
              disabled
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
              aria-describedby="role-description"
            />
            <p id="role-description" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Role is assigned by administrators
            </p>
          </div>
        </div>
      </section>

      {/* Theme Settings */}
      <section 
        className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6"
        aria-labelledby="appearance-heading"
      >
        <h2 id="appearance-heading" className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Appearance
        </h2>
        <div>
          <label 
            htmlFor="theme" 
            className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300"
          >
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-describedby="theme-description"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
          </select>
          <p id="theme-description" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Choose your preferred color theme. System will match your device settings.
          </p>
        </div>
      </section>

      {/* Notification Settings */}
      <section 
        className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        aria-labelledby="notifications-heading"
      >
        <h2 id="notifications-heading" className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
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
                className="w-4 h-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 focus:ring-2"
                aria-describedby="email-notifications-description"
              />
            </div>
            <div className="ml-3">
              <label 
                htmlFor="email-notifications" 
                className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer"
              >
                Email notifications
              </label>
              <p id="email-notifications-description" className="text-xs text-gray-500 dark:text-gray-400">
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
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Save notification preferences"
          >
            {isLoading ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </section>
    </div>
  );
}
