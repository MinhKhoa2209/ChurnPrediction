import { parseApiError, ApiError } from './errors';

const DEFAULT_API_URL = 'http://localhost:8000';
const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
const API_V1_PREFIX = process.env.NEXT_PUBLIC_API_V1_PREFIX || '/api/v1';

// Server-side API URL (for SSR and API routes in Docker)
const SERVER_API_URL = process.env.API_URL || RAW_API_URL;

const API_URL =
  typeof window === 'undefined'
    ? SERVER_API_URL  // Use server-side URL when running on server
    : !process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_URL === DEFAULT_API_URL
      ? window.location.origin
      : process.env.NEXT_PUBLIC_API_URL;

export const API_BASE_URL = `${API_URL}${API_V1_PREFIX}`;

interface RequestOptions extends RequestInit {
  token?: string;
  skipErrorHandling?: boolean; // Allow callers to handle errors manually
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { token, skipErrorHandling, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Merge any additional headers from fetchOptions
  if (fetchOptions.headers) {
    const additionalHeaders = fetchOptions.headers as Record<string, string>;
    Object.assign(headers, additionalHeaders);
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      // Parse error response from backend
      const errorData = await response.json().catch(() => ({
        error: {
          code: 'INTERNAL_ERROR',
          message: response.statusText || 'API request failed',
          timestamp: new Date().toISOString(),
        },
      }));

      // Throw ApiError with structured error data
      throw parseApiError(errorData, response.status);
    }

    // Handle empty responses (e.g. 204 No Content from logout)
    const contentLength = response.headers.get('content-length');
    const contentType = response.headers.get('content-type') || '';

    if (
      response.status === 204 ||
      contentLength === '0' ||
      !contentType.includes('application/json')
    ) {
      return null as T;
    }

    // Safely attempt JSON parse — fallback to null for empty bodies
    const text = await response.text();
    if (!text || text.trim().length === 0) {
      return null as T;
    }

    try {
      return JSON.parse(text) as T;
    } catch {
      return null as T;
    }
  } catch (error) {
    // Re-throw ApiError as-is
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw parseApiError(
        {
          error: {
            code: 'SERVICE_UNAVAILABLE',
            message: 'Unable to connect to the server. Please check your internet connection.',
            timestamp: new Date().toISOString(),
          },
        },
        0
      );
    }

    // Handle other errors
    throw parseApiError(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: error instanceof Error ? error.message : 'An unexpected error occurred',
          timestamp: new Date().toISOString(),
        },
      },
      0
    );
  }
}

export const api = {
  get: <T>(endpoint: string, token?: string, options?: Omit<RequestOptions, 'token'>) =>
    apiRequest<T>(endpoint, { method: 'GET', token, ...options }),

  post: <T>(endpoint: string, data?: unknown, token?: string, options?: Omit<RequestOptions, 'token'>) =>
    apiRequest<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      token,
      ...options,
    }),

  put: <T>(endpoint: string, data?: unknown, token?: string, options?: Omit<RequestOptions, 'token'>) =>
    apiRequest<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      token,
      ...options,
    }),

  patch: <T>(endpoint: string, data?: unknown, token?: string, options?: Omit<RequestOptions, 'token'>) =>
    apiRequest<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
      token,
      ...options,
    }),

  delete: <T>(endpoint: string, token?: string, options?: Omit<RequestOptions, 'token'>) =>
    apiRequest<T>(endpoint, { method: 'DELETE', token, ...options }),

  // File upload
  upload: async <T>(
    endpoint: string,
    file: File,
    token?: string,
    onProgress?: (progress: number) => void
  ): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            onProgress(progress);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            reject(
              parseApiError(
                {
                  error: {
                    code: 'INTERNAL_ERROR',
                    message: 'Failed to parse response',
                    timestamp: new Date().toISOString(),
                  },
                },
                xhr.status
              )
            );
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            reject(parseApiError(errorData, xhr.status));
          } catch {
            reject(
              parseApiError(
                {
                  error: {
                    code: 'INTERNAL_ERROR',
                    message: xhr.statusText || 'File upload failed',
                    timestamp: new Date().toISOString(),
                  },
                },
                xhr.status
              )
            );
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(
          parseApiError(
            {
              error: {
                code: 'SERVICE_UNAVAILABLE',
                message: 'Network error during file upload',
                timestamp: new Date().toISOString(),
              },
            },
            0
          )
        );
      });

      xhr.addEventListener('abort', () => {
        reject(
          parseApiError(
            {
              error: {
                code: 'INTERNAL_ERROR',
                message: 'File upload aborted',
                timestamp: new Date().toISOString(),
              },
            },
            0
          )
        );
      });

      xhr.open('POST', `${API_BASE_URL}${endpoint}`);
      
      Object.entries(headers).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });

      xhr.send(formData);
    });
  },
};

export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${RAW_API_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
