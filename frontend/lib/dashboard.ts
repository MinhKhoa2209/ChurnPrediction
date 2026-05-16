import { API_BASE_URL } from './api';

export interface DashboardMetrics {
  total_customers: number;
  churn_rate: number;
  at_risk_count: number;
  churned_count: number;
  retained_count: number;
}

export interface ChurnDistribution {
  churned: number;
  retained: number;
}

export interface MonthlyTrendData {
  month: string;
  churn_count: number;
  total_count: number;
  churn_rate: number;
}

/**
 * Safely parse JSON from a response, returning a fallback on failure.
 */
async function safeJsonParse<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text || text.trim().length === 0) {
    throw new Error('Empty response body');
  }
  return JSON.parse(text) as T;
}

/**
 * Safely extract error detail from a failed response.
 */
async function extractErrorDetail(response: Response, fallbackMessage: string): Promise<string> {
  try {
    const errorData = await safeJsonParse<{ detail?: string }>(response);
    return errorData?.detail || fallbackMessage;
  } catch {
    return `${fallbackMessage} (HTTP ${response.status})`;
  }
}

export async function getDashboardMetrics(token: string): Promise<DashboardMetrics> {
  const response = await fetch(`${API_BASE_URL}/dashboard/metrics`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to fetch dashboard metrics');
    throw new Error(detail);
  }

  return safeJsonParse<DashboardMetrics>(response);
}

export async function getChurnDistribution(token: string): Promise<ChurnDistribution> {
  const response = await fetch(`${API_BASE_URL}/dashboard/churn-distribution`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to fetch churn distribution');
    throw new Error(detail);
  }

  return safeJsonParse<ChurnDistribution>(response);
}

export async function getMonthlyChurnTrend(
  token: string,
  months: number = 12
): Promise<MonthlyTrendData[]> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/monthly-trend?months=${months}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const detail = await extractErrorDetail(response, 'Failed to fetch monthly churn trend');
    throw new Error(detail);
  }

  return safeJsonParse<MonthlyTrendData[]>(response);
}
