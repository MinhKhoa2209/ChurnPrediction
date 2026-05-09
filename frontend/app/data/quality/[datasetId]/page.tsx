'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { api } from '@/lib/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface QualityReport {
  dataset_id: string;
  quality_score: number;
  completeness_score: number;
  validity_score: number;
  total_records: number;
  missing_values: Record<string, number>;
  outliers: Record<string, { count: number; percentage: number }>;
  invalid_categorical: Record<string, { count: number; invalid_values: string[] }>;
  specific_validations: {
    total_charges_convertibility: { count: number; invalid_rows: number[] };
    negative_values: {
      monthly_charges: { count: number; invalid_rows: number[] };
      tenure: { count: number; invalid_rows: number[] };
    };
  };
}

export default function DataQualityPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.datasetId as string;
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQualityReport = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const report = await api.get<QualityReport>(
        `/datasets/${datasetId}/quality`,
        token!
      );
      setQualityReport(report);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load quality report';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, token]);

  useEffect(() => {
    if (!authLoading && token && datasetId) {
      queueMicrotask(() => {
        void fetchQualityReport();
      });
    }
  }, [authLoading, token, datasetId, fetchQualityReport]);

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const getQualityScoreColor = (score: number): string => {
    if (score > 80) return 'text-green-600 dark:text-green-400';
    if (score >= 70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getQualityScoreBgColor = (score: number): string => {
    if (score > 80) return 'bg-green-100 dark:bg-green-900/20';
    if (score >= 70) return 'bg-yellow-100 dark:bg-yellow-900/20';
    return 'bg-red-100 dark:bg-red-900/20';
  };

  const getIssueCounts = () => {
    if (!qualityReport) return [];

    const missingCount = Object.values(qualityReport.missing_values).reduce(
      (sum, count) => sum + count,
      0
    );
    const outlierCount = Object.values(qualityReport.outliers).reduce(
      (sum, info) => sum + info.count,
      0
    );
    const invalidCount = Object.values(qualityReport.invalid_categorical).reduce(
      (sum, info) => sum + info.count,
      0
    );

    return [
      { category: 'Missing Values', count: missingCount, color: '#ef4444' },
      { category: 'Outliers', count: outlierCount, color: '#f59e0b' },
      { category: 'Invalid Categorical', count: invalidCount, color: '#8b5cf6' },
    ];
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="text-gray-900 dark:text-foreground">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-background">
        <nav className="bg-white dark:bg-card shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                  Data Quality Report
                </h1>
              </div>
              <div className="flex items-center">
                <button
                  onClick={handleBackToDashboard}
                  className="text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-primary-foreground"
                >
                  Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                Error Loading Quality Report
              </h2>
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!qualityReport) {
    return null;
  }

  const issueCounts = getIssueCounts();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Data Quality Report
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {user.email} ({user.role})
              </span>
              <button
                onClick={handleBackToDashboard}
                className="text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-primary-foreground"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          {qualityReport.quality_score < 70 && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                    Low Data Quality Warning
                  </h3>
                  <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                    <p>
                      The data quality score is below 70. Please review the issues below and
                      consider cleaning the data before training models.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground mb-6">
              Overall Quality Score
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div
                className={`${getQualityScoreBgColor(
                  qualityReport.quality_score
                )} rounded-lg p-6 text-center`}
              >
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Quality Score
                </p>
                <p
                  className={`text-5xl font-bold ${getQualityScoreColor(
                    qualityReport.quality_score
                  )}`}
                >
                  {qualityReport.quality_score}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">out of 100</p>
              </div>
              <div className="bg-blue-100 dark:bg-blue-900/20 rounded-lg p-6 text-center">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Completeness Score
                </p>
                <p className="text-5xl font-bold text-blue-600 dark:text-blue-400">
                  {qualityReport.completeness_score}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">out of 100</p>
              </div>
              <div className="bg-purple-100 dark:bg-purple-900/20 rounded-lg p-6 text-center">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Validity Score
                </p>
                <p className="text-5xl font-bold text-purple-600 dark:text-purple-400">
                  {qualityReport.validity_score}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">out of 100</p>
              </div>
            </div>
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Records: <span className="font-semibold">{qualityReport.total_records}</span>
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
              Issues by Category
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={issueCounts}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="category" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                  }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {issueCounts.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
              Missing Values by Column
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
                <thead className="bg-gray-50 dark:bg-muted">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Column
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Missing Count
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Percentage
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-card divide-y divide-gray-200 dark:divide-border">
                  {Object.entries(qualityReport.missing_values)
                    .filter(([, count]) => count > 0)
                    .sort(([, a], [, b]) => b - a)
                    .map(([column, count]) => (
                      <tr key={column}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-foreground">
                          {column}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {((count / qualityReport.total_records) * 100).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  {Object.values(qualityReport.missing_values).every((count) => count === 0) && (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400"
                      >
                        No missing values detected
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
              Outliers by Column (IQR Method)
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
                <thead className="bg-gray-50 dark:bg-muted">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Column
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Outlier Count
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Percentage
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-card divide-y divide-gray-200 dark:divide-border">
                  {Object.entries(qualityReport.outliers)
                    .filter(([, info]) => info.count > 0)
                    .sort(([, a], [, b]) => b.count - a.count)
                    .map(([column, info]) => (
                      <tr key={column}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-foreground">
                          {column}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {info.count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {info.percentage}%
                        </td>
                      </tr>
                    ))}
                  {Object.values(qualityReport.outliers).every((info) => info.count === 0) && (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400"
                      >
                        No outliers detected
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
              Invalid Categorical Values
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
                <thead className="bg-gray-50 dark:bg-muted">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Column
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Invalid Count
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Invalid Values
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-card divide-y divide-gray-200 dark:divide-border">
                  {Object.entries(qualityReport.invalid_categorical)
                    .filter(([, info]) => info.count > 0)
                    .sort(([, a], [, b]) => b.count - a.count)
                    .map(([column, info]) => (
                      <tr key={column}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-foreground">
                          {column}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {info.count}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                          {info.invalid_values.length > 0
                            ? info.invalid_values.join(', ')
                            : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  {Object.values(qualityReport.invalid_categorical).every(
                    (info) => info.count === 0
                  ) && (
                    <tr>
                      <td
                        colSpan={3}
                        className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400"
                      >
                        No invalid categorical values detected
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
              Specific Validations
            </h2>
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-foreground mb-2">
                  TotalCharges Convertibility
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Non-convertible values:{' '}
                  <span className="font-semibold">
                    {qualityReport.specific_validations.total_charges_convertibility.count}
                  </span>
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-foreground mb-2">
                  Negative Values
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  MonthlyCharges with negative values:{' '}
                  <span className="font-semibold">
                    {qualityReport.specific_validations.negative_values.monthly_charges.count}
                  </span>
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Tenure with negative values:{' '}
                  <span className="font-semibold">
                    {qualityReport.specific_validations.negative_values.tenure.count}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
