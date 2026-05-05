/**
 * Screen Reader Announcer Component
 * Requirement 28.6: Screen reader announcements for dynamic content updates
 * 
 * Provides a centralized system for announcing dynamic content changes
 * to screen readers using ARIA live regions.
 */

'use client';

import { useEffect, useState } from 'react';
import { create } from 'zustand';

// Announcement types
export type AnnouncementPriority = 'polite' | 'assertive' | 'off';

export interface Announcement {
  id: string;
  message: string;
  priority: AnnouncementPriority;
  timestamp: number;
}

// Zustand store for managing announcements
interface AnnouncementStore {
  announcements: Announcement[];
  addAnnouncement: (message: string, priority?: AnnouncementPriority) => void;
  clearAnnouncements: () => void;
}

export const useAnnouncementStore = create<AnnouncementStore>((set) => ({
  announcements: [],
  addAnnouncement: (message: string, priority: AnnouncementPriority = 'polite') => {
    const announcement: Announcement = {
      id: `announcement-${Date.now()}-${Math.random()}`,
      message,
      priority,
      timestamp: Date.now(),
    };
    
    set((state) => ({
      announcements: [...state.announcements, announcement],
    }));

    // Auto-clear after 5 seconds
    setTimeout(() => {
      set((state) => ({
        announcements: state.announcements.filter((a) => a.id !== announcement.id),
      }));
    }, 5000);
  },
  clearAnnouncements: () => set({ announcements: [] }),
}));

/**
 * Screen Reader Announcer Component
 * Should be placed once at the root level of the application
 */
export function ScreenReaderAnnouncer() {
  const announcements = useAnnouncementStore((state) => state.announcements);
  const [politeMessages, setPoliteMessages] = useState<string[]>([]);
  const [assertiveMessages, setAssertiveMessages] = useState<string[]>([]);

  useEffect(() => {
    const polite = announcements
      .filter((a) => a.priority === 'polite')
      .map((a) => a.message);
    
    const assertive = announcements
      .filter((a) => a.priority === 'assertive')
      .map((a) => a.message);

    setPoliteMessages(polite);
    setAssertiveMessages(assertive);
  }, [announcements]);

  return (
    <>
      {/* Polite announcements - don't interrupt current speech */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {politeMessages.map((message, index) => (
          <p key={`polite-${index}`}>{message}</p>
        ))}
      </div>

      {/* Assertive announcements - interrupt current speech */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      >
        {assertiveMessages.map((message, index) => (
          <p key={`assertive-${index}`}>{message}</p>
        ))}
      </div>
    </>
  );
}

/**
 * Hook for announcing messages to screen readers
 * Usage:
 * const announce = useScreenReaderAnnounce();
 * announce('Data loaded successfully', 'polite');
 */
export function useScreenReaderAnnounce() {
  const addAnnouncement = useAnnouncementStore((state) => state.addAnnouncement);
  return addAnnouncement;
}

/**
 * Component for announcing route changes
 * Requirement 28.6: Announce page navigation to screen readers
 */
export function RouteAnnouncer({ pageName }: { pageName: string }) {
  const announce = useScreenReaderAnnounce();

  useEffect(() => {
    announce(`Navigated to ${pageName} page`, 'polite');
  }, [pageName, announce]);

  return null;
}

/**
 * Component for announcing loading states
 * Requirement 28.6: Announce async operations to screen readers
 */
interface LoadingAnnouncerProps {
  isLoading: boolean;
  loadingMessage?: string;
  successMessage?: string;
  errorMessage?: string;
  error?: Error | null;
}

export function LoadingAnnouncer({
  isLoading,
  loadingMessage = 'Loading',
  successMessage = 'Content loaded successfully',
  errorMessage = 'An error occurred',
  error = null,
}: LoadingAnnouncerProps) {
  const announce = useScreenReaderAnnounce();
  const [previousLoadingState, setPreviousLoadingState] = useState(isLoading);

  useEffect(() => {
    // Announce when loading starts
    if (isLoading && !previousLoadingState) {
      announce(loadingMessage, 'polite');
    }

    // Announce when loading completes
    if (!isLoading && previousLoadingState) {
      if (error) {
        const message = error.message || errorMessage;
        announce(message, 'assertive');
      } else {
        announce(successMessage, 'polite');
      }
    }

    setPreviousLoadingState(isLoading);
  }, [isLoading, previousLoadingState, loadingMessage, successMessage, errorMessage, error, announce]);

  return null;
}

/**
 * Component for announcing form validation errors
 * Requirement 28.6: Announce validation errors to screen readers
 */
interface ValidationAnnouncerProps {
  errors: Record<string, string>;
}

export function ValidationAnnouncer({ errors }: ValidationAnnouncerProps) {
  const announce = useScreenReaderAnnounce();
  const [previousErrors, setPreviousErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const errorKeys = Object.keys(errors);
    const previousErrorKeys = Object.keys(previousErrors);

    // Announce new errors
    const newErrors = errorKeys.filter((key) => !previousErrorKeys.includes(key));
    if (newErrors.length > 0) {
      const errorMessages = newErrors.map((key) => `${key}: ${errors[key]}`).join('. ');
      announce(`Form validation errors: ${errorMessages}`, 'assertive');
    }

    // Announce cleared errors
    const clearedErrors = previousErrorKeys.filter((key) => !errorKeys.includes(key));
    if (clearedErrors.length > 0 && errorKeys.length === 0) {
      announce('All form errors have been resolved', 'polite');
    }

    setPreviousErrors(errors);
  }, [errors, previousErrors, announce]);

  return null;
}

/**
 * Component for announcing data updates
 * Requirement 28.6: Announce dynamic data changes to screen readers
 */
interface DataUpdateAnnouncerProps {
  data: any;
  dataName: string;
  formatMessage?: (data: any) => string;
}

export function DataUpdateAnnouncer({
  data,
  dataName,
  formatMessage,
}: DataUpdateAnnouncerProps) {
  const announce = useScreenReaderAnnounce();
  const [previousData, setPreviousData] = useState(data);

  useEffect(() => {
    if (data !== previousData && data !== null && data !== undefined) {
      const message = formatMessage
        ? formatMessage(data)
        : `${dataName} has been updated`;
      
      announce(message, 'polite');
      setPreviousData(data);
    }
  }, [data, previousData, dataName, formatMessage, announce]);

  return null;
}

/**
 * Component for announcing notifications
 * Requirement 28.6: Announce in-app notifications to screen readers
 */
interface NotificationAnnouncerProps {
  notification: {
    title: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
  } | null;
}

export function NotificationAnnouncer({ notification }: NotificationAnnouncerProps) {
  const announce = useScreenReaderAnnounce();

  useEffect(() => {
    if (notification) {
      const priority = notification.type === 'error' || notification.type === 'warning'
        ? 'assertive'
        : 'polite';
      
      const message = `${notification.type} notification: ${notification.title}. ${notification.message}`;
      announce(message, priority);
    }
  }, [notification, announce]);

  return null;
}
