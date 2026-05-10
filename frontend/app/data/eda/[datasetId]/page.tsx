'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
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

interface CorrelationData {
  datasetId: string;
  features: string[];
  correlationMatrix: number[][];
  recordCount: number;
}

interface FeatureDistribution {
  bins: number[];
  frequencies: number[];
  min: number;
  max: number;
  mean: number;
  median: number;
}

interface HistogramBin {
  bin: string;
  frequency: number;
}

interface DistributionsData {
  datasetId: string;
  distributions: {
    tenure: FeatureDistribution;
    MonthlyCharges: FeatureDistribution;
    TotalCharges: FeatureDistribution;
  };
  recordCount: number;
}

interface ChurnRateItem {
  contractType?: string;
  internetServiceType?: string;
  churnRate: number;
  totalCustomers: number;
  churnedCustomers: number;
}

interface ChurnByContractData {
  datasetId: string;
  churnRates: ChurnRateItem[];
  recordCount: number;
}

interface ChurnByInternetData {
  datasetId: string;
  churnRates: ChurnRateItem[];
  recordCount: number;
}

interface ScatterDataPoint {
  monthlyCharges: number;
  totalCharges: number;
  churn: boolean;
}

interface ScatterPlotData {
  datasetId: string;
  scatterData: ScatterDataPoint[];
  recordCount: number;
}

interface PCADataPoint2D {
  pc1: number;
  pc2: number;
  churn: boolean;
}

interface PCADataPoint3D {
  pc1: number;
  pc2: number;
  pc3: number;
  churn: boolean;
}

interface PCAData {
  datasetId: string;
  pca2d: PCADataPoint2D[];
  pca3d: PCADataPoint3D[];
  explainedVariance2d: number[];
  explainedVariance3d: number[];
  recordCount: number;
}

export default function EDAPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.datasetId as string;
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [correlationData, setCorrelationData] = useState<CorrelationData | null>(null);
  const [distributionsData, setDistributionsData] = useState<DistributionsData | null>(null);
  const [churnByContractData, setChurnByContractData] = useState<ChurnByContractData | null>(null);
  const [churnByInternetData, setChurnByInternetData] = useState<ChurnByInternetData | null>(null);
  const [scatterData, setScatterData] = useState<ScatterPlotData | null>(null);
  const [pcaData, setPcaData] = useState<PCAData | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const fetchAllEDAData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      setLoadingProgress(0);

      const startTime = Date.now();

      const [correlation, distributions, churnContract, churnInternet, scatter, pca] = await Promise.all([
        api.get<CorrelationData>(`/eda/${datasetId}/correlation`, token!).then(data => {
          setLoadingProgress(prev => prev + 16.67);
          return data;
        }),
        api.get<DistributionsData>(`/eda/${datasetId}/distributions?bins=10`, token!).then(data => {
          setLoadingProgress(prev => prev + 16.67);
          return data;
        }),
        api.get<ChurnByContractData>(`/eda/${datasetId}/churn-by-contract`, token!).then(data => {
          setLoadingProgress(prev => prev + 16.67);
          return data;
        }),
        api.get<ChurnByInternetData>(`/eda/${datasetId}/churn-by-internet`, token!).then(data => {
          setLoadingProgress(prev => prev + 16.67);
          return data;
        }),
        api.get<ScatterPlotData>(`/eda/${datasetId}/scatter`, token!).then(data => {
          setLoadingProgress(prev => prev + 16.67);
          return data;
        }),
        api.get<PCAData>(`/eda/${datasetId}/pca`, token!).then(data => {
          setLoadingProgress(prev => prev + 16.67);
          return data;
        }),
      ]);

      const endTime = Date.now();
      const loadTime = (endTime - startTime) / 1000;

      console.log(`EDA data loaded in ${loadTime.toFixed(2)} seconds`);

      setCorrelationData(correlation);
      setDistributionsData(distributions);
      setChurnByContractData(churnContract);
      setChurnByInternetData(churnInternet);
      setScatterData(scatter);
      setPcaData(pca);
      setLoadingProgress(100);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load EDA data';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, token]);

  useEffect(() => {
    if (!authLoading && token && datasetId) {
      queueMicrotask(() => {
        void fetchAllEDAData();
      });
    }
  }, [authLoading, token, datasetId, fetchAllEDAData]);

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const prepareHistogramData = (distribution: FeatureDistribution) => {
    const data: HistogramBin[] = [];
    for (let i = 0; i < distribution.frequencies.length; i++) {
      const binStart = distribution.bins[i];
      const binEnd = distribution.bins[i + 1];
      const binLabel = `${binStart.toFixed(0)}-${binEnd.toFixed(0)}`;
      data.push({
        bin: binLabel,
        frequency: distribution.frequencies[i],
      });
    }
    return data;
  };

  const getCorrelationColor = (value: number): string => {
    if (value > 0.7) return '#10b981';
    if (value > 0.3) return '#84cc16';
    if (value > -0.3) return '#fbbf24';
    if (value > -0.7) return '#f97316';
    return '#ef4444';
  };

  if (authLoading || isLoading) {
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
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                Error Loading EDA Data
              </h2>
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
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
                    <BarChart data={prepareHistogramData(distributionsData.distributions.tenure)}>
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
                    <BarChart data={prepareHistogramData(distributionsData.distributions.MonthlyCharges)}>
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
                    <BarChart data={prepareHistogramData(distributionsData.distributions.TotalCharges)}>
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
                    data={scatterData.scatterData.filter(d => !d.churn)}
                    fill="#10b981"
                    fillOpacity={0.6}
                  />
                  <Scatter
                    name="Churned"
                    data={scatterData.scatterData.filter(d => d.churn)}
                    fill="#ef4444"
                    fillOpacity={0.6}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}

          {pcaData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-card shadow rounded-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-2">
                  2D PCA Visualization
                </h2>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
                  Explained Variance: PC1 {(pcaData.explainedVariance2d[0] * 100).toFixed(2)}%, 
                  PC2 {(pcaData.explainedVariance2d[1] * 100).toFixed(2)}%
                </p>
                <ResponsiveContainer width="100%" height={350}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis
                      type="number"
                      dataKey="pc1"
                      name="PC1"
                      stroke="#9ca3af"
                      label={{ value: 'Principal Component 1', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="pc2"
                      name="PC2"
                      stroke="#9ca3af"
                      label={{ value: 'Principal Component 2', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '0.5rem',
                      }}
                    />
                    <Legend />
                    <Scatter
                      name="No Churn"
                      data={pcaData.pca2d.filter(d => !d.churn)}
                      fill="#10b981"
                      fillOpacity={0.6}
                    />
                    <Scatter
                      name="Churned"
                      data={pcaData.pca2d.filter(d => d.churn)}
                      fill="#ef4444"
                      fillOpacity={0.6}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white dark:bg-card shadow rounded-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-2">
                  3D PCA Visualization (PC1 vs PC3)
                </h2>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
                  Explained Variance: PC1 {(pcaData.explainedVariance3d[0] * 100).toFixed(2)}%, 
                  PC2 {(pcaData.explainedVariance3d[1] * 100).toFixed(2)}%, 
                  PC3 {(pcaData.explainedVariance3d[2] * 100).toFixed(2)}%
                </p>
                <ResponsiveContainer width="100%" height={350}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis
                      type="number"
                      dataKey="pc1"
                      name="PC1"
                      stroke="#9ca3af"
                      label={{ value: 'Principal Component 1', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="pc3"
                      name="PC3"
                      stroke="#9ca3af"
                      label={{ value: 'Principal Component 3', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '0.5rem',
                      }}
                    />
                    <Legend />
                    <Scatter
                      name="No Churn"
                      data={pcaData.pca3d.filter(d => !d.churn)}
                      fill="#10b981"
                      fillOpacity={0.6}
                    />
                    <Scatter
                      name="Churned"
                      data={pcaData.pca3d.filter(d => d.churn)}
                      fill="#ef4444"
                      fillOpacity={0.6}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
