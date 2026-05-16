/**
 * Model History Page
 * Displays model history table showing all model versions:
 * - Training timestamp, dataset size, hyperparameters, metrics
 * - Filter by model type
 * - Sort by training timestamp descending
 * - Version detail modal
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { listModelVersions, type ModelVersionListItem } from '@/lib/models';
import { getDataset, type Dataset } from '@/lib/datasets';

export default function ModelHistoryPage() {
  const router = useRouter();
  const { token, user } = useAuthStore();

  const [models, setModels] = useState<ModelVersionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modelTypeFilter, setModelTypeFilter] = useState<string>('All');
  const [selectedModel, setSelectedModel] = useState<ModelVersionListItem | null>(null);
  const [datasetCache, setDatasetCache] = useState<Record<string, Dataset>>({});

  useEffect(() => {
    if (!token) return;

    const fetchModels = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await listModelVersions(token, {
          model_type: modelTypeFilter === 'All' ? undefined : modelTypeFilter,
          sort_by: 'trained_at',
          sort_order: 'desc',
        });

        setModels(response.versions);

        // Fetch dataset information for each model
        const datasetIds = [...new Set(response.versions.map(m => m.dataset_id))];
        const datasets: Record<string, Dataset> = {};
        
        await Promise.all(
          datasetIds.map(async (datasetId) => {
            try {
              const dataset = await getDataset(datasetId, token);
              datasets[datasetId] = dataset;
            } catch (err) {
              console.error(`Error fetching dataset ${datasetId}:`, err);
            }
          })
        );
        
        setDatasetCache(datasets);
      } catch (err) {
        console.error('Error fetching models:', err);
        setError(err instanceof Error ? err.message : 'Failed to load model history');
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, [token, modelTypeFilter]);

  const handleViewDetails = (model: ModelVersionListItem) => {
    setSelectedModel(model);
  };

  const handleCloseModal = () => {
    setSelectedModel(null);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadgeColor = (status: string) => {
    return status === 'active'
      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      : 'bg-gray-100 text-gray-800 dark:bg-muted dark:text-gray-300';
  };

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-900 dark:text-foreground">Loading model history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="bg-white dark:bg-card shadow rounded-lg p-6 max-w-md">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      {/* Navigation */}
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Model History
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/models/comparison')}
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
              >
                Compare Models
              </button>
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {user.email} ({user.role})
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Filter Controls - Requirement 15.5 */}
          <div className="bg-white dark:bg-card shadow rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Filter by Model Type:
                </label>
                <select
                  value={modelTypeFilter}
                  onChange={(e) => setModelTypeFilter(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-muted text-gray-900 dark:text-foreground"
                >
                  <option value="All">All Models</option>
                  <option value="KNN">KNN</option>
                  <option value="NaiveBayes">Naive Bayes</option>
                  <option value="DecisionTree">Decision Tree</option>
                  <option value="SVM">SVM</option>
                </select>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {models.length} version{models.length !== 1 ? 's' : ''} found
              </p>
            </div>
          </div>

          {/* Model History Table - Requirement 15.4 */}
          {models.length === 0 ? (
            <div className="bg-white dark:bg-card shadow rounded-lg p-8 text-center">
              <div className="mb-4">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-foreground mb-2">
                No Model Versions Found
              </h3>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                {modelTypeFilter === 'All'
                  ? 'No models have been trained yet.'
                  : `No ${modelTypeFilter} models found. Try selecting a different model type.`}
              </p>
              {modelTypeFilter === 'All' && (
                <button
                  onClick={() => router.push('/models/training')}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-primary-foreground bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Start Training
                </button>
              )}
            </div>
          ) : (
            <div className="bg-white dark:bg-card shadow rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
                  <thead className="bg-gray-50 dark:bg-background">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Model Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Version ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Training Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Dataset Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Accuracy
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        F1-Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-card divide-y divide-gray-200 dark:divide-border">
                    {models.map((model) => (
                      <tr key={model.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-foreground">
                          {model.model_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300 font-mono">
                          {model.version.slice(0, 12)}...
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {formatDate(model.trained_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                          {datasetCache[model.dataset_id]
                            ? `${datasetCache[model.dataset_id].record_count.toLocaleString()} records`
                            : 'Loading...'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-foreground">
                          {(model.metrics.accuracy * 100).toFixed(2)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-foreground">
                          {(model.metrics.f1_score * 100).toFixed(2)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(
                              model.status
                            )}`}
                          >
                            {model.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => handleViewDetails(model)}
                            className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Version Detail Modal */}
      {selectedModel && (
        <div className="fixed inset-0 bg-background bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-card rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-card border-b border-gray-200 dark:border-border px-6 py-4 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Model Version Details
              </h3>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="px-6 py-4 space-y-6">
              {/* Basic Information */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-3">
                  Basic Information
                </h4>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Model Type
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                      {selectedModel.model_type}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Version ID
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-foreground font-mono break-all">
                      {selectedModel.version}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Training Timestamp
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                      {formatDate(selectedModel.trained_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Training Time
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                      {selectedModel.training_time_seconds.toFixed(2)} seconds
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Status
                    </dt>
                    <dd className="mt-1">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(
                          selectedModel.status
                        )}`}
                      >
                        {selectedModel.status}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Classification Threshold
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                      {selectedModel.classification_threshold}
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Metrics */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-3">
                  Performance Metrics
                </h4>
                <dl className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-gray-50 dark:bg-muted rounded-lg p-3">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Accuracy
                    </dt>
                    <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-foreground">
                      {(selectedModel.metrics.accuracy * 100).toFixed(2)}%
                    </dd>
                  </div>
                  <div className="bg-gray-50 dark:bg-muted rounded-lg p-3">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Precision
                    </dt>
                    <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-foreground">
                      {(selectedModel.metrics.precision * 100).toFixed(2)}%
                    </dd>
                  </div>
                  <div className="bg-gray-50 dark:bg-muted rounded-lg p-3">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      Recall
                    </dt>
                    <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-foreground">
                      {(selectedModel.metrics.recall * 100).toFixed(2)}%
                    </dd>
                  </div>
                  <div className="bg-gray-50 dark:bg-muted rounded-lg p-3">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      F1-Score
                    </dt>
                    <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-foreground">
                      {(selectedModel.metrics.f1_score * 100).toFixed(2)}%
                    </dd>
                  </div>
                  <div className="bg-gray-50 dark:bg-muted rounded-lg p-3">
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      ROC-AUC
                    </dt>
                    <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-foreground">
                      {(selectedModel.metrics.roc_auc * 100).toFixed(2)}%
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Hyperparameters */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-3">
                  Hyperparameters
                </h4>
                <div className="bg-gray-50 dark:bg-muted rounded-lg p-4">
                  <pre className="text-sm text-gray-900 dark:text-foreground overflow-x-auto">
                    {JSON.stringify(selectedModel.hyperparameters, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Dataset Information */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-3">
                  Dataset Information
                </h4>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Dataset ID
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-foreground font-mono break-all">
                      {selectedModel.dataset_id}
                    </dd>
                  </div>
                  {datasetCache[selectedModel.dataset_id] && (
                    <>
                      <div>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Dataset Size
                        </dt>
                        <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                          {datasetCache[selectedModel.dataset_id].record_count.toLocaleString()} records
                        </dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Filename
                        </dt>
                        <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                          {datasetCache[selectedModel.dataset_id].filename}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Uploaded At
                        </dt>
                        <dd className="mt-1 text-sm text-gray-900 dark:text-foreground">
                          {formatDate(datasetCache[selectedModel.dataset_id].uploaded_at)}
                        </dd>
                      </div>
                    </>
                  )}
                </dl>
              </div>
            </div>

            <div className="sticky bottom-0 bg-gray-50 dark:bg-background px-6 py-4 flex justify-end gap-3 border-t border-gray-200 dark:border-border">
              <button
                onClick={() => router.push(`/models/evaluation/${selectedModel.id}`)}
                className="px-4 py-2 text-primary-foreground bg-blue-600 hover:bg-blue-700 rounded font-medium"
              >
                View Full Evaluation
              </button>
              <button
                onClick={handleCloseModal}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-white dark:bg-card hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-border rounded font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
