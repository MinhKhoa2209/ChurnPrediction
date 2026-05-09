'use client';

import { useEffect, useState } from 'react';
import { create } from 'zustand';

export type AnnouncementPriority = 'polite' | 'assertive' | 'off';

export interface Announcement {
  id: string;
  message: string;
  priority: AnnouncementPriority;
  timestamp: number;
}

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

    setTimeout(() => {
      set((state) => ({
        announcements: state.announcements.filter((a) => a.id !== announcement.id),
      }));
    }, 5000);
  },
  clearAnnouncements: () => set({ announcements: [] }),
}));

export function ScreenReaderAnnouncer() {
  const announcements = useAnnouncementStore((state) => state.announcements);
  const politeMessages = announcements
    .filter((a) => a.priority === 'polite')
    .map((a) => a.message);

  const assertiveMessages = announcements
    .filter((a) => a.priority === 'assertive')
    .map((a) => a.message);

  return (
    <>
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

export function useScreenReaderAnnounce() {
  const addAnnouncement = useAnnouncementStore((state) => state.addAnnouncement);
  return addAnnouncement;
}

export function RouteAnnouncer({ pageName }: { pageName: string }) {
  const announce = useScreenReaderAnnounce();

  useEffect(() => {
    announce(`Navigated to ${pageName} page`, 'polite');
  }, [pageName, announce]);

  return null;
}

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
    if (isLoading && !previousLoadingState) {
      announce(loadingMessage, 'polite');
    }

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

interface ValidationAnnouncerProps {
  errors: Record<string, string>;
}

export function ValidationAnnouncer({ errors }: ValidationAnnouncerProps) {
  const announce = useScreenReaderAnnounce();
  const [previousErrors, setPreviousErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const errorKeys = Object.keys(errors);
    const previousErrorKeys = Object.keys(previousErrors);

    const newErrors = errorKeys.filter((key) => !previousErrorKeys.includes(key));
    if (newErrors.length > 0) {
      const errorMessages = newErrors.map((key) => `${key}: ${errors[key]}`).join('. ');
      announce(`Form validation errors: ${errorMessages}`, 'assertive');
    }

    const clearedErrors = previousErrorKeys.filter((key) => !errorKeys.includes(key));
    if (clearedErrors.length > 0 && errorKeys.length === 0) {
      announce('All form errors have been resolved', 'polite');
    }

    setPreviousErrors(errors);
  }, [errors, previousErrors, announce]);

  return null;
}

interface DataUpdateAnnouncerProps {
  data: unknown;
  dataName: string;
  formatMessage?: (data: unknown) => string;
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
