/**
 * Model Comparison Page
 * 
 * Displays side-by-side comparison of multiple models:
 * - Comparison table with all metrics
 * - F1-score comparison chart
 * - Training time comparison chart
 * - Sortable columns
 * - Best model highlighting
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { listModelVersions, archiveModelVersion, type ModelVersionListItem } from '@/lib/models';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CHART_TEXT_COLOR = 'var(--muted-foreground)';
const CHART_GRID_COLOR = 'var(--border)';
const PRIMARY_BAR_COLOR = 'var(--primary)';
const SECONDARY_BAR_COLOR = 'var(--chart-2)';

export default function ModelComparisonPage() {
  const router = useRouter();
  const { token, user } = useAuthStore();

  const [models, setModels] = useState<ModelVersionListItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<string>('trained_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [archiveConfirm, setArchiveConfirm] = useState<{ modelId: string; modelName: string; archive: boolean } | null>(null);
  const [archiving, setArchiving] = useState<string | null>(null);

  const filteredModels = useMemo(() => {
    if (!searchQuery.trim()) {
      return models;
    }

    const query = searchQuery.toLowerCase();
    return models.filter(model =>
      model.model_type.toLowerCase().includes(query) ||
      model.version.toLowerCase().includes(query)
    );
  }, [models, searchQuery]);

  useEffect(() => {
    if (!token) return;

    const fetchModels = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await listModelVersions(token, {
          status: 'active',
          sort_by: sortBy,
          sort_order: sortOrder,
        });

        setModels(Array.isArray(response?.versions) ? response.versions : []);
      } catch (err) {
        console.error('Error fetching models:', err);
        setError(err instanceof Error ? err.message : 'Failed to load models');
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, [token, sortBy, sortOrder]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const handleArchiveClick = (model: ModelVersionListItem) => {
    const archive = model.status === 'active';
    setArchiveConfirm({
      modelId: model.id,
      modelName: `${model.model_type} (${model.version.slice(0, 12)}...)`,
      archive
    });
  };

  const handleArchiveConfirm = async () => {
    if (!archiveConfirm || !token) return;

    try {
      setArchiving(archiveConfirm.modelId);
      await archiveModelVersion(archiveConfirm.modelId, archiveConfirm.archive, token);
      
      // Refresh the models list
      const response = await listModelVersions(token, {
        status: 'active',
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setModels(Array.isArray(response?.versions) ? response.versions : []);
      
      setArchiveConfirm(null);
    } catch (err) {
      console.error('Error archiving model:', err);
      setError(err instanceof Error ? err.message : 'Failed to archive model');
    } finally {
      setArchiving(null);
    }
  };

  const handleArchiveCancel = () => {
    setArchiveConfirm(null);
  };

  const getBestModel = (): ModelVersionListItem | null => {
    if (filteredModels.length === 0) return null;
    return filteredModels.reduce((best, current) =>
      current.metrics.f1_score > best.metrics.f1_score ? current : best
    );
  };

  const bestModel = getBestModel();

  // Prepare chart data
  const comparisonChartData = filteredModels.map((model) => ({
    label: model.model_type,
    versionLabel: model.version.slice(0, 12),
    f1_score: parseFloat((model.metrics.f1_score * 100).toFixed(2)),
    time: parseFloat(model.training_time_seconds.toFixed(2)),
  }));

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-foreground">Loading models...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="bg-card shadow rounded-lg p-6 max-w-md">
          <p className="text-destructive">{error}</p>
        </div>
      </div>
    );
  }

  const renderChartTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{ payload: { label: string; versionLabel: string; f1_score: number; time: number } }>;
  }) => {
    if (!active || !payload?.length) {
      return null;
    }

    const data = payload[0].payload;

    return (
      <div className="rounded-lg border border-border bg-popover px-3 py-2 text-sm text-popover-foreground shadow">
        <p className="font-medium">{data.label}</p>
        <p className="text-muted-foreground">Version: {data.versionLabel}</p>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-primary hover:text-primary/80 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-bold text-foreground">
                Model Comparison
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/models/history')}
                className="text-sm text-primary hover:text-primary/80 font-medium"
              >
                View History
              </button>
              <span className="text-sm text-muted-foreground">
                {user.email} ({user.role})
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {models.length === 0 ? (
            <div className="bg-card shadow rounded-lg p-8 text-center">
              <div className="mb-4">
                <svg
                  className="mx-auto h-12 w-12 text-muted-foreground"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">
                No Models Available
              </h3>
              <p className="text-muted-foreground mb-4">
                No active models found. {user.role === 'Admin' ? 'Train some models first to see comparisons.' : 'Please contact your administrator to train models.'}
              </p>
              {user.role === 'Admin' && (
              <button
                onClick={() => router.push('/models/training')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring"
              >
                Start Training
              </button>
              )}
            </div>
          ) : (
            <>
              {/* Comparison Table - Requirement 11.1 */}
              <div className="bg-card shadow rounded-lg p-6 mb-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold text-foreground">
                    Model Performance Comparison
                  </h2>
                  <div className="flex items-center gap-4">
                    <input
                      type="text"
                      placeholder="Search models..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="px-4 py-2 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                    <p className="text-sm text-muted-foreground whitespace-nowrap">
                      {filteredModels.length} of {models.length} model{models.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Model Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Version
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent select-none"
                          onClick={() => handleSort('accuracy')}
                          title="Click to sort by Accuracy"
                        >
                          <div className="flex items-center gap-1">
                            Accuracy
                            {sortBy === 'accuracy' && (
                              <span className="text-primary font-bold">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent select-none"
                          onClick={() => handleSort('precision')}
                          title="Click to sort by Precision"
                        >
                          <div className="flex items-center gap-1">
                            Precision
                            {sortBy === 'precision' && (
                              <span className="text-primary font-bold">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent select-none"
                          onClick={() => handleSort('recall')}
                          title="Click to sort by Recall"
                        >
                          <div className="flex items-center gap-1">
                            Recall
                            {sortBy === 'recall' && (
                              <span className="text-primary font-bold">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent select-none"
                          onClick={() => handleSort('f1_score')}
                          title="Click to sort by F1-Score"
                        >
                          <div className="flex items-center gap-1">
                            F1-Score
                            {sortBy === 'f1_score' && (
                              <span className="text-primary font-bold">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent select-none"
                          onClick={() => handleSort('roc_auc')}
                          title="Click to sort by ROC-AUC"
                        >
                          <div className="flex items-center gap-1">
                            ROC-AUC
                            {sortBy === 'roc_auc' && (
                              <span className="text-primary font-bold">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th
                          className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:bg-accent select-none"
                          onClick={() => handleSort('training_time_seconds')}
                          title="Click to sort by Training Time"
                        >
                          <div className="flex items-center gap-1">
                            Training Time
                            {sortBy === 'training_time_seconds' && (
                              <span className="text-primary font-bold">
                                {sortOrder === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-card divide-y divide-border">
                      {filteredModels.length === 0 ? (
                        <tr>
                          <td colSpan={9} className="px-6 py-8 text-center text-muted-foreground">
                            {searchQuery ? 'No models match your search.' : 'No models found.'}
                          </td>
                        </tr>
                      ) : (
                        filteredModels.map((model) => (
                        <tr
                          key={model.id}
                          className={
                            bestModel?.id === model.id
                              ? 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500'
                              : ''
                          }
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">
                            {model.model_type}
                            {bestModel?.id === model.id && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                ⭐ Best
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground font-mono">
                            {model.version.slice(0, 12)}...
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                            {(model.metrics.accuracy * 100).toFixed(2)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                            {(model.metrics.precision * 100).toFixed(2)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                            {(model.metrics.recall * 100).toFixed(2)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-foreground">
                            {(model.metrics.f1_score * 100).toFixed(2)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                            {(model.metrics.roc_auc * 100).toFixed(2)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                            {model.training_time_seconds.toFixed(2)}s
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => router.push(`/models/evaluation/${model.id}`)}
                                className="text-primary hover:text-primary/80 font-medium"
                              >
                                View Details
                              </button>
                              {user.role === 'Admin' && (
                                <button
                                  onClick={() => handleArchiveClick(model)}
                                  disabled={archiving === model.id}
                                  className="text-muted-foreground hover:text-foreground font-medium disabled:opacity-50"
                                  title={model.status === 'active' ? 'Archive model' : 'Unarchive model'}
                                >
                                  {archiving === model.id ? 'Processing...' : (model.status === 'active' ? 'Archive' : 'Unarchive')}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* F1-Score Comparison Chart - Requirement 11.3 */}
                <div className="bg-card shadow rounded-lg p-6">
                  <h2 className="text-xl font-bold text-foreground mb-4">
                    F1-Score Comparison
                  </h2>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={comparisonChartData}>
                        <CartesianGrid stroke={CHART_GRID_COLOR} strokeDasharray="3 3" />
                        <XAxis
                          dataKey="label"
                          interval={0}
                          tick={{ fill: CHART_TEXT_COLOR, fontSize: 12 }}
                        />
                        <YAxis
                          label={{
                            value: 'F1-Score (%)',
                            angle: -90,
                            position: 'insideLeft',
                            fill: CHART_TEXT_COLOR,
                          }}
                          tick={{ fill: CHART_TEXT_COLOR }}
                        />
                        <Tooltip content={renderChartTooltip} />
                        <Bar dataKey="f1_score" fill={PRIMARY_BAR_COLOR} name="F1-Score (%)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Training Time Comparison Chart - Requirement 11.4 */}
                <div className="bg-card shadow rounded-lg p-6">
                  <h2 className="text-xl font-bold text-foreground mb-4">
                    Training Time Comparison
                  </h2>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={comparisonChartData}>
                        <CartesianGrid stroke={CHART_GRID_COLOR} strokeDasharray="3 3" />
                        <XAxis
                          dataKey="label"
                          interval={0}
                          tick={{ fill: CHART_TEXT_COLOR, fontSize: 12 }}
                        />
                        <YAxis
                          label={{
                            value: 'Time (seconds)',
                            angle: -90,
                            position: 'insideLeft',
                            fill: CHART_TEXT_COLOR,
                          }}
                          tick={{ fill: CHART_TEXT_COLOR }}
                        />
                        <Tooltip content={renderChartTooltip} />
                        <Bar dataKey="time" fill={SECONDARY_BAR_COLOR} name="Training Time (s)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Archive Confirmation Dialog */}
      {archiveConfirm && (
        <div className="fixed inset-0 bg-background/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-foreground mb-4">
              {archiveConfirm.archive ? 'Archive Model' : 'Unarchive Model'}
            </h3>
            <p className="text-muted-foreground mb-6">
              {archiveConfirm.archive
                ? `Are you sure you want to archive ${archiveConfirm.modelName}? Archived models will not appear in the active models list.`
                : `Are you sure you want to unarchive ${archiveConfirm.modelName}? This will make it available for predictions again.`}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleArchiveCancel}
                disabled={archiving !== null}
                className="px-4 py-2 text-muted-foreground bg-muted hover:bg-accent rounded font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleArchiveConfirm}
                disabled={archiving !== null}
                className={`px-4 py-2 text-primary-foreground rounded font-medium disabled:opacity-50 ${
                  archiveConfirm.archive
                    ? 'bg-orange-600 hover:bg-orange-700'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {archiving !== null ? 'Processing...' : (archiveConfirm.archive ? 'Archive' : 'Unarchive')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
