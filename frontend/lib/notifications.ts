import { API_BASE_URL } from './api';

export interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface UnreadCount {
  unread_count: number;
}

export async function listNotifications(
  token: string,
  unreadOnly: boolean = false
): Promise<Notification[]> {
  const response = await fetch(
    `${API_BASE_URL}/notifications?unread_only=${unreadOnly}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list notifications');
  }

  return response.json();
}

export async function getUnreadCount(token: string): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get unread count');
  }

  const data: UnreadCount = await response.json();
  return data.unread_count;
}

export async function markAsRead(
  token: string,
  notificationId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/notifications/${notificationId}/read`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to mark notification as read');
  }
}

export async function markAllAsRead(token: string): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/notifications/mark-all-read`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to mark all notifications as read');
  }

  const data = await response.json();
  return data.marked_count;
}
