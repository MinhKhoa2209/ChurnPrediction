import { api } from './api';
import type { User } from './auth';

export async function listUsers(token: string): Promise<User[]> {
  return api.get<User[]>('/users', token);
}

export async function getUser(userId: string, token: string): Promise<User> {
  return api.get<User>(`/users/${userId}`, token);
}

export async function deleteUser(userId: string, token: string): Promise<void> {
  return api.delete<void>(`/users/${userId}`, token);
}
