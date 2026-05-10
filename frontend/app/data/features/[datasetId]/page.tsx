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

interface FeatureImportanceItem {
  featureName: string;
  importanceScore: number;
}

interface FeatureImportanceResponse {
  datasetId: string;
  featureImportance: FeatureImportanceItem[];
  recordCount: number;
}

interface FeatureSelectionResponse {
  datasetId: string;
  selectedFeatures: FeatureImportanceItem[];
  selectionMethod: string;
  threshold?: number;
}

interface InteractionFeatureItem {
  featureName: string;
  formula: string;
  description: string;
  statistics: {
    mean: number;
    std: number;
    min: number;
    max: number;
    median: number;
  };
}

interface InteractionFeaturesResponse {
  datasetId: string;
  interactionFeatures: InteractionFeatureItem[];
  recordCount: number;
}

export default function FeatureEngineeringPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.datasetId as string;
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [featureImportance, setFeatureImportance] = useState<FeatureImportanceResponse | null>(null);
  const [selectedFeatures, setSelectedFeatures] = useState<Set<string>>(new Set());
  const [importanceThreshold, setImportanceThreshold] = useState<number>(0.05);
  const [useThreshold, setUseThreshold] = useState<boolean>(false);
  const [interactionFeatures, setInteractionFeatures] = useState<InteractionFeaturesResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingInteraction, setIsCreatingInteraction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const canModifyFeatures = user?.role === 'Admin';

  const fetchFeatureImportance = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await api.get<FeatureImportanceResponse>(
        `/features/${datasetId}/importance`,
        token!
      );

      setFeatureImportance(data);

      const allFeatureNames = new Set(data.featureImportance.map(f => f.featureName));
      setSelectedFeatures(allFeatureNames);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load feature importance';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, token]);

  useEffect(() => {
    if (!authLoading && token && datasetId) {
      queueMicrotask(() => {
        void fetchFeatureImportance();
      });
    }
  }, [authLoading, token, datasetId, fetchFeatureImportance]);

  const handleFeatureToggle = (featureName: string) => {
    if (!canModifyFeatures) return;

    setSelectedFeatures(prev => {
      const newSet = new Set(prev);
      if (newSet.has(featureName)) {
        newSet.delete(featureName);
      } else {
        newSet.add(featureName);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (!canModifyFeatures || !featureImportance) return;

    const allFeatureNames = new Set(featureImportance.featureImportance.map(f => f.featureName));
    setSelectedFeatures(allFeatureNames);
  };

  const handleDeselectAll = () => {
    if (!canModifyFeatures) return;
    setSelectedFeatures(new Set());
  };

  const handleThresholdChange = (value: number) => {
    setImportanceThreshold(value);
    
    if (useThreshold && featureImportance) {
      const selected = new Set(
        featureImportance.featureImportance
          .filter(f => f.importanceScore >= value)
          .map(f => f.featureName)
      );
      setSelectedFeatures(selected);
    }
  };

  const handleUseThresholdToggle = () => {
    const newUseThreshold = !useThreshold;
    setUseThreshold(newUseThreshold);

    if (newUseThreshold && featureImportance) {
      const selected = new Set(
        featureImportance.featureImportance
          .filter(f => f.importanceScore >= importanceThreshold)
          .map(f => f.featureName)
      );
      setSelectedFeatures(selected);
    }
  };

  const handleSaveSelection = async () => {
    if (!canModifyFeatures) {
      setError('You do not have permission to save feature selection');
      return;
    }

    if (selectedFeatures.size === 0) {
      setError('Please select at least one feature');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const requestBody = useThreshold
        ? { importanceThreshold }
        : { selectedFeatures: Array.from(selectedFeatures) };

      const response = await api.post<FeatureSelectionResponse>(
        `/features/${datasetId}/select`,
        requestBody,
        token!
      );

      setSuccessMessage(
        `Successfully saved ${response.selectedFeatures.length} features using ${response.selectionMethod} method`
      );

      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save feature selection';
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateInteractionFeatures = async () => {
    if (!canModifyFeatures) {
      setError('You do not have permission to create interaction features');
      return;
    }

    try {
      setIsCreatingInteraction(true);
      setError(null);
      setSuccessMessage(null);

      const response = await api.post<InteractionFeaturesResponse>(
        `/features/${datasetId}/interactions`,
        {},
        token!
      );

      setInteractionFeatures(response);
      setSuccessMessage(
        `Successfully created ${response.interactionFeatures.length} interaction feature(s)`
      );

      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create interaction features';
      setError(errorMessage);
    } finally {
      setIsCreatingInteraction(false);
    }
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const getSelectedStats = () => {
    if (!featureImportance) return { count: 0, totalImportance: 0 };

    const selectedItems = featureImportance.featureImportance.filter(f =>
      selectedFeatures.has(f.featureName)
    );

    return {
      count: selectedItems.length,
      totalImportance: selectedItems.reduce((sum, f) => sum + f.importanceScore, 0),
    };
  };

  const selectedStats = getSelectedStats();

  const chartData = featureImportance?.featureImportance.map(f => ({
    ...f,
    isSelected: selectedFeatures.has(f.featureName),
  })) || [];

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-background">
        <div className="text-gray-900 dark:text-foreground mb-4">Loading feature importance...</div>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (error && !featureImportance) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-background">
        <nav className="bg-white dark:bg-card shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                  Feature Engineering
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
                Error Loading Feature Data
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
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Feature Engineering
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
          {successMessage && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <p className="text-sm text-green-800 dark:text-green-200">{successMessage}</p>
            </div>
          )}

          {error && featureImportance && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground mb-2">
              Feature Importance Analysis
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Dataset ID: <span className="font-mono">{datasetId}</span>
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Total Records: <span className="font-semibold">{featureImportance?.recordCount || 0}</span>
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Total Features: <span className="font-semibold">{featureImportance?.featureImportance.length || 0}</span>
            </p>
          </div>

          {featureImportance && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-4">
                Feature Importance Scores
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                Features ranked by mutual information score. Higher scores indicate stronger relationships with churn prediction.
              </p>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis type="number" stroke="#9ca3af" />
                  <YAxis
                    type="category"
                    dataKey="featureName"
                    stroke="#9ca3af"
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '0.5rem',
                    }}
                    formatter={(value) => Number(value).toFixed(4)}
                  />
                  <Bar dataKey="importanceScore" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.isSelected ? '#3b82f6' : '#9ca3af'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {featureImportance && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-foreground">
                  Feature Selection
                </h2>
                {!canModifyFeatures && (
                  <span className="text-sm text-yellow-600 dark:text-yellow-400">
                    View Only - Requires Admin role
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <p className="text-sm text-blue-600 dark:text-blue-400 mb-1">Selected Features</p>
                  <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {selectedStats.count}
                  </p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <p className="text-sm text-green-600 dark:text-green-400 mb-1">Total Importance</p>
                  <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {selectedStats.totalImportance.toFixed(4)}
                  </p>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                  <p className="text-sm text-purple-600 dark:text-purple-400 mb-1">Selection Method</p>
                  <p className="text-lg font-bold text-purple-900 dark:text-purple-100">
                    {useThreshold ? 'Threshold' : 'Manual'}
                  </p>
                </div>
              </div>

              {canModifyFeatures && (
                <div className="mb-6 p-4 bg-gray-50 dark:bg-muted rounded-lg">
                  <div className="flex items-center mb-4">
                    <input
                      type="checkbox"
                      id="useThreshold"
                      checked={useThreshold}
                      onChange={handleUseThresholdToggle}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label
                      htmlFor="useThreshold"
                      className="ml-2 text-sm font-medium text-gray-900 dark:text-foreground"
                    >
                      Use importance threshold for auto-selection
                    </label>
                  </div>

                  {useThreshold && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Importance Threshold: {importanceThreshold.toFixed(3)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="0.5"
                        step="0.01"
                        value={importanceThreshold}
                        onChange={(e) => handleThresholdChange(parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-muted"
                      />
                      <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-1">
                        <span>0.000</span>
                        <span>0.500</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {canModifyFeatures && !useThreshold && (
                <div className="flex space-x-2 mb-4">
                  <button
                    onClick={handleSelectAll}
                    className="px-4 py-2 bg-blue-600 text-primary-foreground rounded-lg hover:bg-blue-700 transition-colors text-sm"
                  >
                    Select All
                  </button>
                  <button
                    onClick={handleDeselectAll}
                    className="px-4 py-2 bg-gray-600 text-primary-foreground rounded-lg hover:bg-gray-700 transition-colors text-sm"
                  >
                    Deselect All
                  </button>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                {featureImportance.featureImportance.map((feature) => (
                  <div
                    key={feature.featureName}
                    className={`flex items-center p-3 rounded-lg border ${
                      selectedFeatures.has(feature.featureName)
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                        : 'bg-gray-50 dark:bg-muted border-gray-300 dark:border-border'
                    }`}
                  >
                    <input
                      type="checkbox"
                      id={feature.featureName}
                      checked={selectedFeatures.has(feature.featureName)}
                      onChange={() => handleFeatureToggle(feature.featureName)}
                      disabled={!canModifyFeatures || useThreshold}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label
                      htmlFor={feature.featureName}
                      className="ml-3 flex-1 cursor-pointer"
                    >
                      <span className="block text-sm font-medium text-gray-900 dark:text-foreground">
                        {feature.featureName}
                      </span>
                      <span className="block text-xs text-gray-600 dark:text-gray-400">
                        Importance: {feature.importanceScore.toFixed(4)}
                      </span>
                    </label>
                  </div>
                ))}
              </div>

              {canModifyFeatures && (
                <button
                  onClick={handleSaveSelection}
                  disabled={isSaving || selectedFeatures.size === 0}
                  className="w-full px-6 py-3 bg-green-600 text-primary-foreground rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isSaving ? 'Saving...' : `Save Selection (${selectedStats.count} features)`}
                </button>
              )}
            </div>
          )}

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-4">
              Interaction Features
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Create interaction features that capture relationships between multiple features.
              Currently supports: tenure × MonthlyCharges
            </p>

            {canModifyFeatures && (
              <button
                onClick={handleCreateInteractionFeatures}
                disabled={isCreatingInteraction}
                className="mb-6 px-6 py-3 bg-purple-600 text-primary-foreground rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isCreatingInteraction ? 'Creating...' : 'Create Interaction Features'}
              </button>
            )}

            {!canModifyFeatures && (
              <p className="text-sm text-yellow-600 dark:text-yellow-400 mb-6">
                Requires Admin role to create interaction features
              </p>
            )}

            {interactionFeatures && (
              <div className="space-y-4">
                {interactionFeatures.interactionFeatures.map((feature) => (
                  <div
                    key={feature.featureName}
                    className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg"
                  >
                    <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-100 mb-2">
                      {feature.featureName}
                    </h3>
                    <p className="text-sm text-purple-700 dark:text-purple-300 mb-2">
                      <span className="font-medium">Formula:</span> {feature.formula}
                    </p>
                    <p className="text-sm text-purple-700 dark:text-purple-300 mb-3">
                      {feature.description}
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      <div>
                        <p className="text-xs text-purple-600 dark:text-purple-400">Mean</p>
                        <p className="text-sm font-semibold text-purple-900 dark:text-purple-100">
                          {feature.statistics.mean.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-purple-600 dark:text-purple-400">Std Dev</p>
                        <p className="text-sm font-semibold text-purple-900 dark:text-purple-100">
                          {feature.statistics.std.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-purple-600 dark:text-purple-400">Min</p>
                        <p className="text-sm font-semibold text-purple-900 dark:text-purple-100">
                          {feature.statistics.min.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-purple-600 dark:text-purple-400">Max</p>
                        <p className="text-sm font-semibold text-purple-900 dark:text-purple-100">
                          {feature.statistics.max.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-purple-600 dark:text-purple-400">Median</p>
                        <p className="text-sm font-semibold text-purple-900 dark:text-purple-100">
                          {feature.statistics.median.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
