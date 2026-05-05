/**
 * Dashboard Page
 * Protected route - requires authentication

'use client';

import { useAuthStore } from '@/lib/store/auth-store';
import { logout } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  getDashboardMetrics,
  getChurnDistribution,
  getMonthlyChurnTrend,
  type DashboardMetrics,
  type ChurnDistribution,
  type MonthlyTrendData,
} from '@/lib/dashboard';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Navigation } from '@/components/Navigation';
import { AccessibleChart } from '@/components/AccessibleChart';
import { announceToScreenReader } from '@/lib/accessibility';
import { WelcomeModal } from '@/components/WelcomeModal';
import { Tooltip as InfoTooltip } from '@/components/Tooltip';

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, isLoading, clearAuth } = useAuthStore();
  
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [distribution, setDistribution] = useState<ChurnDistribution | null>(null);
  const [trendData, setTrendData] = useState<MonthlyTrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Bugfix: Wait for authentication state to be restored before loading data
  useEffect(() => {
    if (!isLoading && token && user) {
      loadDashboardData();
    }
  }, [isLoading, token, user]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  const loadDashboardData = async () => {
    if (!token) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [metricsData, distributionData, trendDataResult] = await Promise.all([
        getDashboardMetrics(token),
        getChurnDistribution(token),
        getMonthlyChurnTrend(token, 12),
      ]);
      
      setMetrics(metricsData);
      setDistribution(distributionData);
      setTrendData(trendDataResult);
      
      // Requirement 28.6: Announce data load to screen readers
      announceToScreenReader('Dashboard data loaded successfully', 'polite');
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(errorMessage);
      
      // Requirement 28.6: Announce error to screen readers
      announceToScreenReader(`Error loading dashboard: ${errorMessage}`, 'assertive');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (token) {
      try {
        await logout(token);
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    clearAuth();
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-gray-900 dark:text-white" role="status" aria-live="polite">
          Loading...
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // AuthProvider will handle redirect
  }

  // Colors for charts
  const COLORS = {
    churned: '#ef4444', // red-500
    retained: '#10b981', // green-500
    trend: '#3b82f6', // blue-500
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <WelcomeModal />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Dashboard Header */}
          <header className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Dashboard Analytics
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Overview of customer churn metrics and trends
            </p>
          </header>

          {/* Error State */}
          {error && (
            <div 
              className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
              role="alert"
              aria-live="assertive"
            >
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              <button
                onClick={loadDashboardData}
                className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
                aria-label="Retry loading dashboard data"
              >
                Try again
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
              <div className="text-gray-600 dark:text-gray-400">Loading dashboard data...</div>
            </div>
          )}

          {/* Dashboard Content */}
          {!loading && metrics && (
            <>
              {/* Metrics Cards - Requirement 2.1 */}
              <section aria-labelledby="metrics-heading" className="mb-6">
                <h2 id="metrics-heading" className="sr-only">Key Metrics</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Total Customers */}
                  <article className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 bg-blue-500 rounded-md p-3" aria-hidden="true">
                      <svg
                        className="h-6 w-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                      </svg>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          Total Customers
                        </dt>
                        <dd className="text-3xl font-semibold text-gray-900 dark:text-white">
                          {metrics.total_customers.toLocaleString()}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </article>

                {/* Churn Rate */}
                <article className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                  <div className="flex items-center">
                    <div className={`flex-shrink-0 rounded-md p-3 ${
                      metrics.churn_rate < 20 ? 'bg-green-500' :
                      metrics.churn_rate < 30 ? 'bg-yellow-500' : 'bg-red-500'
                    }`} aria-hidden="true">
                      <svg
                        className="h-6 w-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          Churn Rate
                        </dt>
                        <dd className="text-3xl font-semibold text-gray-900 dark:text-white">
                          {metrics.churn_rate.toFixed(1)}%
                        </dd>
                      </dl>
                    </div>
                  </div>
                </article>

                {/* At-Risk Customers */}
                <article className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 bg-orange-500 rounded-md p-3" aria-hidden="true">
                      <svg
                        className="h-6 w-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                      </svg>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                          At-Risk Customers
                        </dt>
                        <dd className="text-3xl font-semibold text-gray-900 dark:text-white">
                          {metrics.at_risk_count.toLocaleString()}
                        </dd>
                        <dd className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Probability &gt; 70%
                        </dd>
                      </dl>
                    </div>
                  </div>
                </article>
              </div>
            </section>

              {/* Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Churn Distribution Chart - Requirement 2.3 */}
                {distribution && (
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Churn Distribution
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Churned', value: distribution.churned },
                            { name: 'Retained', value: distribution.retained },
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={(props: any) =>
                            `${props.name}: ${(props.percent * 100).toFixed(1)}%`
                          }
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          <Cell fill={COLORS.churned} />
                          <Cell fill={COLORS.retained} />
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Monthly Churn Trend - Requirement 2.4 */}
                {trendData.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Monthly Churn Trend
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={trendData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="month"
                          tick={{ fill: '#9ca3af' }}
                          tickFormatter={(value) => {
                            const [year, month] = value.split('-');
                            return `${month}/${year.slice(2)}`;
                          }}
                        />
                        <YAxis tick={{ fill: '#9ca3af' }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1f2937',
                            border: 'none',
                            borderRadius: '0.5rem',
                            color: '#fff',
                          }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="churn_rate"
                          stroke={COLORS.trend}
                          strokeWidth={2}
                          name="Churn Rate (%)"
                          dot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Quick Actions */}
          {(user.role === 'Admin' || user.role === 'Data_Scientist') && (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <InfoTooltip content="Upload customer data in CSV format to train models">
                  <button
                    onClick={() => router.push('/data/upload')}
                    className="flex items-center justify-center px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors w-full"
                  >
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    Upload Dataset
                  </button>
                </InfoTooltip>
                <InfoTooltip content="Compare performance metrics across different models">
                  <button
                    onClick={() => router.push('/models/comparison')}
                    className="flex items-center justify-center px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors w-full"
                  >
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    Compare Models
                  </button>
                </InfoTooltip>
                <InfoTooltip content="Predict churn probability for individual customers">
                  <button
                    onClick={() => router.push('/predictions/single')}
                    className="flex items-center justify-center px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors w-full"
                  >
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                      />
                    </svg>
                    Make Prediction
                  </button>
                </InfoTooltip>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
