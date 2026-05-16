import { API_BASE_URL } from './api';

export interface ReportGenerateRequest {
  model_version_id: string;
  include_confusion_matrix?: boolean;
  include_roc_curve?: boolean;
  include_feature_importance?: boolean;
}

export interface Report {
  id: string;
  model_version_id: string;
  report_type: string;
  file_size: number;
  created_at: string;
}

/**
 * Safely extract error detail from a failed response.
 */
async function extractErrorDetail(response: Response, fallbackMessage: string): Promise<string> {
  try {
    const text = await response.text();
    if (!text || text.trim().length === 0) {
      return `${fallbackMessage} (HTTP ${response.status})`;
    }
    const data = JSON.parse(text);
    return data?.detail || data?.message || fallbackMessage;
  } catch {
    return `${fallbackMessage} (HTTP ${response.status})`;
  }
}

/**
 * Safely parse JSON from a successful response.
 */
async function safeJsonParse<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text || text.trim().length === 0) {
    throw new Error('Empty response body');
  }
  return JSON.parse(text) as T;
}

export async function generateReport(
  token: string,
  request: ReportGenerateRequest
): Promise<Report> {
  const response = await fetch(`${API_BASE_URL}/reports/generate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to generate report');
    throw new Error(detail);
  }
  return safeJsonParse<Report>(response);
}

export async function listReports(token: string): Promise<Report[]> {
  const response = await fetch(`${API_BASE_URL}/reports`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to list reports');
    throw new Error(detail);
  }
  
  // Handle empty array response
  const text = await response.text();
  if (!text || text.trim().length === 0 || text.trim() === '[]') {
    return [];
  }
  
  try {
    return JSON.parse(text) as Report[];
  } catch (error) {
    console.error('Failed to parse reports response:', error);
    return [];
  }
}

export async function getReport(token: string, reportId: string): Promise<Report> {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to get report');
    throw new Error(detail);
  }
  return safeJsonParse<Report>(response);
}

export async function downloadReport(token: string, reportId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/download`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to download report');
    throw new Error(detail);
  }
  // Trigger browser download
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `report_${reportId}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
