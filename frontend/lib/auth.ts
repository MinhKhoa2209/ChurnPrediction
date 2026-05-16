import { api } from './api';

export interface User {
  id: string;
  email: string;
  role: 'Admin' | 'Analyst';
  name: string | null;
  avatar: string | null;
  provider: string;
  created_at: string;
  email_verified: boolean;
  email_notifications_enabled: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface GoogleAuthRequest {
  credential: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  return api.post<AuthResponse>('/auth/register', data);
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  return api.post<AuthResponse>('/auth/login', data);
}

export async function adminLogin(data: AdminLoginRequest): Promise<AuthResponse> {
  // Admin login uses the same endpoint as regular login
  // Role check happens on frontend after successful login
  return api.post<AuthResponse>('/auth/login', data);
}

export async function googleAuth(data: GoogleAuthRequest): Promise<AuthResponse> {
  return api.post<AuthResponse>('/auth/google', data);
}

export async function logout(token: string): Promise<void> {
  await api.post('/auth/logout', undefined, token);
}

export async function getCurrentUser(token: string): Promise<User> {
  return api.get<User>('/auth/me', token);
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<{ message: string }> {
  return api.post<{ message: string }>('/auth/forgot-password', data);
}

export async function resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
  return api.post<{ message: string }>('/auth/reset-password', data);
}
