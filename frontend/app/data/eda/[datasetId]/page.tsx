'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import {
  useEDAStore,
  type CorrelationData,
  type DistributionsData,
  type ChurnByContractData,
  type ChurnByInternetData,
  type ScatterPlotData,
  type FeatureDistribution,
} from '@/lib/store/eda-store';
import { api } from '@/lib/api';
import {
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface HistogramBin {
  bin: string;
  frequency: number;
}

export default function EDAPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.datasetId as string;
  const { user, token, isLoading: authLoading } = useAuthStore();

  // EDA store for caching
  const {
    getCachedData,
    setCachedData,
    isCacheValid,
    setLoading: setStoreLoading,
    isLoading: isStoreLoading,
  } = useEDAStore();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isNotReady, setIsNotReady] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);

  // Guard against StrictMode double-fetch and duplicate calls
  const fetchStarted = useRef(false);

  // Read cached data (these are derived, not state)
  const cached = getCachedData(datasetId);
  const correlationData = cached?.correlationData ?? null;
  const distributionsData = cached?.distributionsData ?? null;
  const churnByContractData = cached?.churnByContractData ?? null;
  const churnByInternetData = cached?.churnByInternetData ?? null;
  const scatterData = cached?.scatterData ?? null;

  const fetchAllEDAData = useCallback(async () => {
    // Skip if already loading or cache is valid
    if (isStoreLoading(datasetId)) {
      console.log(`[EDA] Already loading dataset ${datasetId}, skipping`);
      return;
    }

    if (isCacheValid(datasetId)) {
      console.log(`[EDA] Using cached data for dataset ${datasetId}`);
      setIsLoading(false);
      setLoadingProgress(100);
      return;
    }

    try {
      setIsLoading(true);
      setStoreLoading(datasetId, true);
      setError(null);
      setIsNotReady(false);
      setLoadingProgress(0);

      console.log(`[EDA] Fetching EDA data for dataset ${datasetId}...`);
      const startTime = Date.now();

      // 5 parallel API calls (PCA removed)
      const [correlation, distributions, churnContract, churnInternet, scatter] = await Promise.all([
        api.get<CorrelationData>(`/eda/${datasetId}/correlation`, token!).then(data => {
          setLoadingProgress(prev => prev + 20);
          return data;
        }),
        api.get<DistributionsData>(`/eda/${datasetId}/distributions?bins=10`, token!).then(data => {
          setLoadingProgress(prev => prev + 20);
          return data;
        }),
        api.get<ChurnByContractData>(`/eda/${datasetId}/churn-by-contract`, token!).then(data => {
          setLoadingProgress(prev => prev + 20);
          return data;
        }),
        api.get<ChurnByInternetData>(`/eda/${datasetId}/churn-by-internet`, token!).then(data => {
          setLoadingProgress(prev => prev + 20);
          return data;
        }),
        api.get<ScatterPlotData>(`/eda/${datasetId}/scatter`, token!).then(data => {
          setLoadingProgress(prev => prev + 20);
          return data;
        }),
      ]);

      const loadTime = ((Date.now() - startTime) / 1000).toFixed(2);
      console.log(`[EDA] All data loaded in ${loadTime}s — ${correlation?.recordCount} records`);

      // Cache in Zustand store (survives unmount)
      setCachedData(datasetId, {
        correlationData: correlation,
        distributionsData: distributions,
        churnByContractData: churnContract,
        churnByInternetData: churnInternet,
        scatterData: scatter,
      });

      setLoadingProgress(100);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load EDA data';
      console.error(`[EDA] Error:`, err);

      if (errorMessage.toLowerCase().includes('not ready') || errorMessage.toLowerCase().includes('processing')) {
        setIsNotReady(true);
        setError('Dataset is still being processed. Please wait for processing to complete before viewing EDA.');
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
      setStoreLoading(datasetId, false);
    }
  }, [datasetId, token, isCacheValid, isStoreLoading, setCachedData, setStoreLoading]);

  useEffect(() => {
    if (!authLoading && token && datasetId && !fetchStarted.current) {
      fetchStarted.current = true;
      queueMicrotask(() => {
        void fetchAllEDAData();
      });
    }
  }, [authLoading, token, datasetId, fetchAllEDAData]);

  // ── Memoized chart data transforms ──────────────────────────────

  const prepareHistogramData = useCallback((distribution: FeatureDistribution): HistogramBin[] => {
    const data: HistogramBin[] = [];
    for (let i = 0; i < distribution.frequencies.length; i++) {
      const binStart = distribution.bins[i];
      const binEnd = distribution.bins[i + 1];
      data.push({
        bin: `${binStart.toFixed(0)}-${binEnd.toFixed(0)}`,
        frequency: distribution.frequencies[i],
      });
    }
    return data;
  }, []);

  const tenureHistogram = useMemo(
    () => distributionsData ? prepareHistogramData(distributionsData.distributions.tenure) : [],
    [distributionsData, prepareHistogramData]
  );

  const monthlyChargesHistogram = useMemo(
    () => distributionsData ? prepareHistogramData(distributionsData.distributions.MonthlyCharges) : [],
    [distributionsData, prepareHistogramData]
  );

  const totalChargesHistogram = useMemo(
    () => distributionsData ? prepareHistogramData(distributionsData.distributions.TotalCharges) : [],
    [distributionsData, prepareHistogramData]
  );

  const scatterNoChurn = useMemo(
    () => scatterData?.scatterData.filter(d => !d.churn) ?? [],
    [scatterData]
  );

  const scatterChurned = useMemo(
    () => scatterData?.scatterData.filter(d => d.churn) ?? [],
    [scatterData]
  );

  // ── Churn distribution summary ──────────────────────────────────

  const churnSummary = useMemo(() => {
    if (!churnByContractData) return null;
    const totalCustomers = churnByContractData.churnRates.reduce((a, b) => a + b.totalCustomers, 0);
    const totalChurned = churnByContractData.churnRates.reduce((a, b) => a + b.churnedCustomers, 0);
    return {
      totalCustomers,
      totalChurned,
      totalRetained: totalCustomers - totalChurned,
      overallChurnRate: totalCustomers > 0 ? totalChurned / totalCustomers : 0,
    };
  }, [churnByContractData]);

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const getCorrelationColor = (value: number): string => {
    if (value > 0.7) return '#10b981';
    if (value > 0.3) return '#84cc16';
    if (value > -0.3) return '#fbbf24';
    if (value > -0.7) return '#f97316';
    return '#ef4444';
  };

  // ── Render states ───────────────────────────────────────────────

  if (authLoading || (isLoading && !cached)) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-background">
        <div className="text-gray-900 dark:text-foreground mb-4">Loading EDA visualizations...</div>
        <div className="w-64 bg-gray-200 dark:bg-muted rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${loadingProgress}%` }}
          />
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          {loadingProgress.toFixed(0)}%
        </div>
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
                  Exploratory Data Analysis
                </h1>
              </div>
              <div className="flex items-center">
                <button
                  onClick={handleBackToDashboard}
                  className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  ← Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            {isNotReady ? (
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-amber-800 dark:text-amber-200 mb-2">
                  Dataset Still Processing
                </h2>
                <p className="text-sm text-amber-700 dark:text-amber-300 mb-4">
                  {error}
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => router.push(`/data/processing?dataset=${datasetId}`)}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-sm font-medium"
                  >
                    View Processing Status
                  </button>
                  <button
                    onClick={() => { fetchStarted.current = false; setError(null); void fetchAllEDAData(); }}
                    className="px-4 py-2 border border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300 rounded-md text-sm font-medium hover:bg-amber-100 dark:hover:bg-amber-900/30"
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                  Error Loading EDA Data
                </h2>
                <p className="text-sm text-red-700 dark:text-red-300 mb-4">{error}</p>
                <button
                  onClick={() => { fetchStarted.current = false; setError(null); void fetchAllEDAData(); }}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium"
                >
                  Retry
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={handleBackToDashboard}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Exploratory Data Analysis
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">

          {/* Dataset Overview + Churn Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground mb-2">
                Dataset Overview
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Dataset ID: <span className="font-mono">{datasetId}</span>
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Records: <span className="font-semibold">{correlationData?.recordCount || 0}</span>
              </p>
            </div>

            {churnSummary && (
              <>
                <div className="bg-white dark:bg-card shadow rounded-lg p-6">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Churn Rate</h3>
                  <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                    {(churnSummary.overallChurnRate * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {churnSummary.totalChurned.toLocaleString()} of {churnSummary.totalCustomers.toLocaleString()} customers
                  </p>
                </div>
                <div className="bg-white dark:bg-card shadow rounded-lg p-6">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Retained</h3>
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {(((1 - churnSummary.overallChurnRate) * 100)).toFixed(1)}%
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {churnSummary.totalRetained.toLocaleString()} customers retained
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Correlation Heatmap */}
          {correlationData && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
                Correlation Heatmap
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Shows relationships between numeric features. Darker colors indicate stronger correlations.
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="border border-gray-300 dark:border-border p-2"></th>
                      {correlationData.features.map((feature) => (
                        <th
                          key={feature}
                          className="border border-gray-300 dark:border-border p-2 text-xs font-medium text-gray-700 dark:text-gray-300"
                        >
                          {feature}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {correlationData.features.map((feature, i) => (
                      <tr key={feature}>
                        <td className="border border-gray-300 dark:border-border p-2 text-xs font-medium text-gray-700 dark:text-gray-300">
                          {feature}
                        </td>
                        {correlationData.features.map((_, j) => {
                          const value = correlationData.correlationMatrix[i][j];
                          const color = getCorrelationColor(value);
                          return (
                            <td
                              key={j}
                              className="border border-gray-300 dark:border-border p-2 text-center text-xs"
                              style={{
                                backgroundColor: color,
                                color: Math.abs(value) > 0.5 ? '#ffffff' : '#000000',
                              }}
                            >
                              {value.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Feature Distributions */}
          {distributionsData && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
                Feature Distributions
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-2">
                    Tenure (months)
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    Mean: {distributionsData.distributions.tenure.mean.toFixed(2)} | 
                    Median: {distributionsData.distributions.tenure.median.toFixed(2)}
                  </p>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={tenureHistogram}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="bin" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '0.5rem',
                        }}
                      />
                      <Bar dataKey="frequency" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-2">
                    Monthly Charges ($)
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    Mean: ${distributionsData.distributions.MonthlyCharges.mean.toFixed(2)} | 
                    Median: ${distributionsData.distributions.MonthlyCharges.median.toFixed(2)}
                  </p>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={monthlyChargesHistogram}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="bin" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '0.5rem',
                        }}
                      />
                      <Bar dataKey="frequency" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-2">
                    Total Charges ($)
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    Mean: ${distributionsData.distributions.TotalCharges.mean.toFixed(2)} | 
                    Median: ${distributionsData.distributions.TotalCharges.median.toFixed(2)}
                  </p>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={totalChargesHistogram}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="bin" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '0.5rem',
                        }}
                      />
                      <Bar dataKey="frequency" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Churn Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {churnByContractData && (
              <div className="bg-white dark:bg-card shadow rounded-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
                  Churn Rate by Contract Type
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={churnByContractData.churnRates}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="contractType" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '0.5rem',
                      }}
                      formatter={(value) => `${(Number(value) * 100).toFixed(2)}%`}
                    />
                    <Bar dataKey="churnRate" fill="#ef4444" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {churnByInternetData && (
              <div className="bg-white dark:bg-card shadow rounded-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
                  Churn Rate by Internet Service
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={churnByInternetData.churnRates}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="internetServiceType" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '0.5rem',
                      }}
                      formatter={(value) => `${(Number(value) * 100).toFixed(2)}%`}
                    />
                    <Bar dataKey="churnRate" fill="#f59e0b" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Scatter Plot */}
          {scatterData && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-6">
                Monthly Charges vs Total Charges (Colored by Churn)
              </h2>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    type="number"
                    dataKey="monthlyCharges"
                    name="Monthly Charges"
                    stroke="#9ca3af"
                    label={{ value: 'Monthly Charges ($)', position: 'insideBottom', offset: -5 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="totalCharges"
                    name="Total Charges"
                    stroke="#9ca3af"
                    label={{ value: 'Total Charges ($)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '0.5rem',
                    }}
                    cursor={{ strokeDasharray: '3 3' }}
                  />
                  <Legend />
                  <Scatter
                    name="No Churn"
                    data={scatterNoChurn}
                    fill="#10b981"
                    fillOpacity={0.6}
                  />
                  <Scatter
                    name="Churned"
                    data={scatterChurned}
                    fill="#ef4444"
                    fillOpacity={0.6}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
