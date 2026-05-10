'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '@/lib/store/auth-store';
import { useTheme } from 'next-themes';
import { API_BASE_URL } from '@/lib/api';
import { Camera, User } from 'lucide-react';

export default function SettingsPage() {
  const { user, token, setAuth } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [name, setName] = useState('');
  const [avatar, setAvatar] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) {
      queueMicrotask(() => {
        setEmailNotifications(user.email_notifications_enabled || false);
        setName(user.name || '');
        setAvatar(user.avatar || '');
      });
    }
  }, [user]);

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setSaveMessage({ type: 'error', text: 'Please select an image file' });
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      setSaveMessage({ type: 'error', text: 'Image size must be less than 2MB' });
      return;
    }

    // Convert to base64
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result as string;
      setAvatar(base64String);
    };
    reader.readAsDataURL(file);
  };

  const handleSaveProfile = async () => {
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
          name: name.trim() || null,
          avatar: avatar || null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save profile settings');
      }

      const updatedUser = await response.json();
      
      // Update auth store with new user data
      if (user) {
        setAuth({
          ...user,
          name: updatedUser.name,
          avatar: updatedUser.avatar,
          email_notifications_enabled: updatedUser.email_notifications_enabled,
        }, token);
      }

      setSaveMessage({ type: 'success', text: 'Profile updated successfully' });
      
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Error saving profile settings:', error);
      setSaveMessage({ type: 'error', text: 'Failed to save profile settings' });
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
          {/* Avatar Upload */}
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div 
                className="w-24 h-24 rounded-full bg-muted flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
                onClick={handleAvatarClick}
              >
                {avatar ? (
                  <img 
                    src={avatar} 
                    alt="User avatar" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-12 h-12 text-muted-foreground" />
                )}
              </div>
              <button
                type="button"
                onClick={handleAvatarClick}
                className="absolute bottom-0 right-0 p-2 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                aria-label="Upload avatar"
              >
                <Camera className="w-4 h-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
                aria-label="Avatar file input"
              />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Profile Picture</p>
              <p className="text-xs text-muted-foreground">
                Click to upload a new avatar (max 2MB)
              </p>
            </div>
          </div>

          {/* Name Input */}
          <div>
            <label 
              htmlFor="name" 
              className="block text-sm font-medium mb-2 text-muted-foreground"
            >
              Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-3 py-2 border border-border rounded-lg bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              aria-describedby="name-description"
            />
            <p id="name-description" className="mt-1 text-xs text-muted-foreground">
              Your display name
            </p>
          </div>

          {/* Email (Read-only) */}
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

          {/* Role (Read-only) */}
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
            onClick={handleSaveProfile}
            disabled={isLoading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Save profile settings"
          >
            {isLoading ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </section>
    </div>
  );
}
