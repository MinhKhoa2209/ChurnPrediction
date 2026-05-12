'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import {
  createSinglePrediction,
  type PredictionInput,
  type PredictionResponse,
} from '@/lib/predictions';
import { listModelVersions, type ModelVersionListItem } from '@/lib/models';
import PredictionForm from '@/components/predictions/prediction-form';
import PredictionResult from '@/components/predictions/prediction-result';
import { AlertTriangle, AlertCircle, BarChart3 } from 'lucide-react';

export default function PredictionsPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [modelVersions, setModelVersions] = useState<ModelVersionListItem[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [isPredicting, setIsPredicting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedModel = modelVersions.find((model) => model.id === selectedModelId);

  useEffect(() => {
    if (!token) return;

    const fetchModels = async () => {
      try {
        setIsLoadingModels(true);
        setError(null);
        const response = await listModelVersions(token, { status: 'active' });
        const versions = Array.isArray(response?.versions) ? response.versions : [];
        setModelVersions(versions);
        
        if (versions.length > 0) {
          setSelectedModelId(versions[0].id);
        }
      } catch (err) {
        console.error('Error loading model versions:', err);
        setError(err instanceof Error ? err.message : 'Failed to load model versions');
      } finally {
        setIsLoadingModels(false);
      }
    };

    fetchModels();
  }, [token]);

  const handleFormSubmit = async (input: PredictionInput) => {
    if (!token || !selectedModelId) {
      setError('Please select a model version');
      return;
    }

    try {
      setIsPredicting(true);
      setError(null);

      const result = await createSinglePrediction(
        {
          model_version_id: selectedModelId,
          input,
        },
        token
      );

      setPrediction(result);
    } catch (err) {
      console.error('Error creating prediction:', err);
      setError(err instanceof Error ? err.message : 'Failed to create prediction');
      setPrediction(null);
    } finally {
      setIsPredicting(false);
    }
  };

  const handleReset = () => {
    setPrediction(null);
    setError(null);
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const formatMetric = (value?: number) =>
    typeof value === 'number' && Number.isFinite(value) ? value.toFixed(3) : 'N/A';

  const formatThreshold = (value?: number) =>
    typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : 'N/A';

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="text-gray-900 dark:text-foreground">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
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
                Customer Churn Prediction
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/predictions/batch')}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              >
                Batch Predictions
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
          <div className="bg-white dark:bg-card shadow rounded-lg p-6 mb-6">
            <h2 className="text-lg font-bold text-gray-900 dark:text-foreground mb-4">
              Select Model Version
            </h2>
            
            {isLoadingModels ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">Loading models...</span>
              </div>
            ) : modelVersions.length === 0 ? (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-center">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                      No Active Models Available
                    </p>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                      Please train a model first before making predictions.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <select
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-border rounded-lg bg-white dark:bg-muted text-gray-900 dark:text-foreground focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {modelVersions.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.model_type} - v{model.version.slice(0, 8)} (F1: {formatMetric(model.metrics?.f1_score)}, Accuracy: {formatMetric(model.metrics?.accuracy)})
                    </option>
                  ))}
                </select>
                
                {selectedModelId && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      <strong>Selected Model:</strong>{' '}
                      {selectedModel?.model_type ?? 'Unknown'}
                    </p>
                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                      Threshold: {formatThreshold(selectedModel?.classification_threshold)}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <PredictionForm
                onSubmit={handleFormSubmit}
                isSubmitting={isPredicting}
                disabled={!selectedModelId || modelVersions.length === 0}
              />
            </div>

            <div>
              {prediction ? (
                <PredictionResult
                  prediction={prediction}
                  onReset={handleReset}
                />
              ) : (
                <div className="bg-white dark:bg-card shadow rounded-lg p-6 h-full flex items-center justify-center">
                  <div className="text-center text-gray-500 dark:text-gray-400">
                    <BarChart3
                      className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600"
                    />
                    <p className="text-lg font-medium">No Prediction Yet</p>
                    <p className="text-sm mt-2">
                      Fill out the customer information form and click &quot;Predict Churn&quot; to see results
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 bg-white dark:bg-card shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-4">
              About Churn Prediction
            </h3>
            <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
              <div>
                <p className="font-medium">What is Churn Prediction?</p>
                <p className="text-gray-600 dark:text-gray-400">
                  Churn prediction uses machine learning to identify customers who are likely to discontinue service.
                  This allows proactive retention efforts to be targeted at high-risk customers.
                </p>
              </div>
              <div>
                <p className="font-medium">How to Interpret Results:</p>
                <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 mt-1 space-y-1">
                  <li><strong>Green (Low Risk):</strong> Probability &lt; 30% - Customer is unlikely to churn</li>
                  <li><strong>Yellow (Medium Risk):</strong> Probability 30-70% - Monitor customer engagement</li>
                  <li><strong>Red (High Risk):</strong> Probability &gt; 70% - Immediate retention action recommended</li>
                </ul>
              </div>
              <div>
                <p className="font-medium">Feature Contributions (SHAP Values):</p>
                <p className="text-gray-600 dark:text-gray-400">
                  The waterfall chart shows which customer features contribute most to the churn prediction.
                  Positive contributions (red) increase churn probability, while negative contributions (green) decrease it.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
