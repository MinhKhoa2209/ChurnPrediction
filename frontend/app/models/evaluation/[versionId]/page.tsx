/**
 * Model Evaluation Page
 * 
 * Displays comprehensive evaluation metrics for a specific model version:
 * - Metrics table (accuracy, precision, recall, F1-score, ROC-AUC)
 * - Confusion matrix heatmap
 * - ROC curve chart
 * - Model version selector
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { 
  getModelVersion, 
  getROCCurve,
  listModelVersions,
  archiveModelVersion,
  updateThreshold,
  type ModelVersion,
  type ModelMetrics,
  type ConfusionMatrixData,
  type ROCCurveData,
  type ModelVersionListItem
} from '@/lib/models';
import { generateReport, downloadReport } from '@/lib/reports';
import MetricsTable from '@/components/models/metrics-table';
import ConfusionMatrixHeatmap from '@/components/models/confusion-matrix-heatmap';
import ROCCurveChart from '@/components/models/roc-curve-chart';
import ModelVersionSelector from '@/components/models/model-version-selector';
import ThresholdSlider from '@/components/models/threshold-slider';

export default function ModelEvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const { token, user } = useAuthStore();
  const versionId = params.versionId as string;

  const [modelVersion, setModelVersion] = useState<ModelVersion | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [confusionMatrix, setConfusionMatrix] = useState<ConfusionMatrixData | null>(null);
  const [rocCurve, setROCCurve] = useState<ROCCurveData | null>(null);
  const [rocCurveError, setRocCurveError] = useState<string | null>(null);
  const [modelVersions, setModelVersions] = useState<ModelVersionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [archiveConfirm, setArchiveConfirm] = useState<{ archive: boolean } | null>(null);
  const [archiving, setArchiving] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!token || !versionId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        setRocCurveError(null);

        const [versionResult, versionsResult, rocResult] = await Promise.allSettled([
          getModelVersion(versionId, token),
          listModelVersions(token),
          getROCCurve(versionId, token),
        ]);

        if (versionResult.status !== 'fulfilled') {
          throw versionResult.reason;
        }

        const versionData = versionResult.value;

        setModelVersion(versionData);
        setMetrics(versionData.metrics);
        setConfusionMatrix({
          matrix: versionData.confusion_matrix,
          labels: ['No Churn', 'Churn'],
        });

        if (versionsResult.status === 'fulfilled') {
          setModelVersions(
            Array.isArray(versionsResult.value?.versions) && versionsResult.value.versions.length > 0
              ? versionsResult.value.versions
              : [versionData]
          );
        } else {
          console.warn('Failed to load model versions list:', versionsResult.reason);
          setModelVersions([versionData]);
        }

        if (rocResult.status === 'fulfilled') {
          setROCCurve(rocResult.value);
        } else {
          console.warn('Failed to load ROC curve:', rocResult.reason);
          setROCCurve(null);
          setRocCurveError(
            rocResult.reason instanceof Error
              ? rocResult.reason.message
              : 'ROC curve is temporarily unavailable'
          );
        }
      } catch (err) {
        console.error('Error fetching model evaluation data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load model evaluation data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, versionId]);

  const handleVersionChange = (newVersionId: string) => {
    router.push(`/models/evaluation/${newVersionId}`);
  };

  const handleArchiveClick = () => {
    if (!modelVersion) return;
    const archive = modelVersion.status === 'active';
    setArchiveConfirm({ archive });
  };

  const handleArchiveConfirm = async () => {
    if (!archiveConfirm || !token || !modelVersion) return;

    try {
      setArchiving(true);
      await archiveModelVersion(versionId, archiveConfirm.archive, token);
      
      // Refresh the model version data
      const updatedVersion = await getModelVersion(versionId, token);
      setModelVersion(updatedVersion);
      
      setArchiveConfirm(null);
    } catch (err) {
      console.error('Error archiving model:', err);
      setError(err instanceof Error ? err.message : 'Failed to archive model');
    } finally {
      setArchiving(false);
    }
  };

  const handleArchiveCancel = () => {
    setArchiveConfirm(null);
  };

  const handleThresholdUpdate = async (newThreshold: number) => {
    if (!token || !versionId) {
      throw new Error('Missing authentication token or version ID');
    }

    try {
      await updateThreshold(versionId, newThreshold, token);
      
      // Refresh the model version data to get updated threshold
      const updatedVersion = await getModelVersion(versionId, token);
      setModelVersion(updatedVersion);
    } catch (err) {
      console.error('Error updating threshold:', err);
      throw err; // Re-throw to let the component handle the error
    }
  };

  const handleGenerateReport = async () => {
    if (!token || !versionId) return;
    
    try {
      setGenerating(true);
      setError(null);

      const report = await generateReport(token, {
        model_version_id: versionId,
        include_confusion_matrix: true,
        include_roc_curve: true,
        include_feature_importance: true,
      });

      await downloadReport(token, report.id);
      alert('Report generated and downloaded successfully!');
    } catch (err) {
      console.error('Error generating report:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  if (!user) {
    return null; // AuthProvider will handle redirect
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-900 dark:text-foreground">Loading model evaluation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="bg-white dark:bg-card shadow rounded-lg p-6 max-w-md">
          <div className="flex items-center mb-4">
            <svg
              className="w-6 h-6 text-red-600 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">Error</h2>
          </div>
          <p className="text-gray-700 dark:text-gray-300 mb-4">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="w-full bg-blue-600 hover:bg-blue-700 text-primary-foreground px-4 py-2 rounded font-medium"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!modelVersion || !metrics || !confusionMatrix) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <p className="text-gray-900 dark:text-foreground">No data available</p>
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
                Model Evaluation
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {user.email} ({user.role})
              </span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Model Version Selector */}
          <div className="mb-6">
            <ModelVersionSelector
              versions={modelVersions}
              selectedVersionId={versionId}
              onVersionChange={handleVersionChange}
            />
          </div>

          {/* Model Information Card */}
          <div className="bg-white dark:bg-card shadow rounded-lg p-6 mb-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Model Information
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={handleGenerateReport}
                  disabled={generating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-primary-foreground rounded font-medium disabled:opacity-50"
                >
                  {generating ? 'Generating...' : 'Generate Report'}
                </button>
                {user.role === 'Admin' && (
                  <button
                    onClick={handleArchiveClick}
                    disabled={archiving}
                    className={`px-4 py-2 rounded font-medium text-primary-foreground disabled:opacity-50 ${
                      modelVersion.status === 'active'
                        ? 'bg-orange-600 hover:bg-orange-700'
                        : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {archiving ? 'Processing...' : (modelVersion.status === 'active' ? 'Archive Model' : 'Unarchive Model')}
                  </button>
                )}
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Model Type</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-foreground">
                  {modelVersion.model_type}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Version</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-foreground">
                  {modelVersion.version}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-foreground">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      modelVersion.status === 'active'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-muted dark:text-gray-300'
                    }`}
                  >
                    {modelVersion.status}
                  </span>
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Training Time
                </p>
                <p className="text-lg font-semibold text-gray-900 dark:text-foreground">
                  {modelVersion.training_time_seconds.toFixed(2)}s
                </p>
              </div>
            </div>
          </div>

          {/* Metrics Table - Requirement 10.5 */}
          <div className="mb-6">
            <MetricsTable metrics={metrics} threshold={modelVersion.classification_threshold} />
          </div>

          {/* Threshold Slider - Requirements 12.9, 12.10 (Admin only) */}
          {user.role === 'Admin' && (
            <div className="mb-6">
              <ThresholdSlider
                versionId={versionId}
                currentThreshold={modelVersion.classification_threshold}
                onThresholdUpdate={handleThresholdUpdate}
                disabled={modelVersion.status !== 'active'}
              />
            </div>
          )}

          {/* Visualizations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Confusion Matrix - Requirement 10.4, 10.6 */}
            <div>
              <ConfusionMatrixHeatmap data={confusionMatrix} />
            </div>

            {/* ROC Curve - Requirement 10.6 */}
            <div>
              {rocCurve ? (
                <ROCCurveChart data={rocCurve} />
              ) : (
                <div className="bg-white dark:bg-card shadow rounded-lg p-6 h-full">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-4">
                    ROC Curve
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {rocCurveError || 'ROC curve is temporarily unavailable for this model.'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Hyperparameters */}
          <div className="mt-6 bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-4">
              Hyperparameters
            </h2>
            <div className="bg-gray-50 dark:bg-background rounded p-4">
              <pre className="text-sm text-gray-900 dark:text-foreground overflow-x-auto">
                {JSON.stringify(modelVersion.hyperparameters, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </main>

      {/* Archive Confirmation Dialog */}
      {archiveConfirm && modelVersion && (
        <div className="fixed inset-0 bg-background bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-card rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-foreground mb-4">
              {archiveConfirm.archive ? 'Archive Model' : 'Unarchive Model'}
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              {archiveConfirm.archive
                ? `Are you sure you want to archive ${modelVersion.model_type} (${modelVersion.version.slice(0, 12)}...)? Archived models will not appear in the active models list.`
                : `Are you sure you want to unarchive ${modelVersion.model_type} (${modelVersion.version.slice(0, 12)}...)? This will make it available for predictions again.`}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleArchiveCancel}
                disabled={archiving}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-muted hover:bg-gray-200 dark:hover:bg-gray-600 rounded font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleArchiveConfirm}
                disabled={archiving}
                className={`px-4 py-2 text-primary-foreground rounded font-medium disabled:opacity-50 ${
                  archiveConfirm.archive
                    ? 'bg-orange-600 hover:bg-orange-700'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {archiving ? 'Processing...' : (archiveConfirm.archive ? 'Archive' : 'Unarchive')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
