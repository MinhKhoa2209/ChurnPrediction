/**
 * Churn Prediction Page
 * Provides a comprehensive interface for predicting customer churn:
 * - Form accepting all customer feature inputs (Req 12.1)
 * - Field validation (Req 12.2, 12.3)
 * - Prediction generation (Req 12.4, 12.5, 12.6)
 * - Probability display with color coding (Req 12.7)
 * - SHAP waterfall chart showing feature contributions (Req 12.8)
 * - Threshold slider for Data_Scientist role (Req 12.9, 12.10)
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import {
  createSinglePrediction,
  getProbabilityColor,
  type PredictionInput,
  type PredictionResponse,
} from '@/lib/predictions';
import { listModelVersions, type ModelVersionListItem } from '@/lib/models';
import PredictionForm from '@/components/predictions/prediction-form';
import PredictionResult from '@/components/predictions/prediction-result';

export default function PredictionsPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [modelVersions, setModelVersions] = useState<ModelVersionListItem[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [formData, setFormData] = useState<PredictionInput | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [isPredicting, setIsPredicting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available model versions on mount
  useEffect(() => {
    if (!token) return;

    const fetchModels = async () => {
      try {
        setIsLoadingModels(true);
        setError(null);
        const response = await listModelVersions(token, { status: 'active' });
        setModelVersions(response.versions);
        
        // Auto-select the first active model if available
        if (response.versions.length > 0) {
          setSelectedModelId(response.versions[0].id);
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
      setFormData(input);

      // Create prediction (Requirement 12.5, 12.6)
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
    setFormData(null);
    setError(null);
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-gray-900 dark:text-white">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null; // AuthProvider will handle redirect
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={handleBackToDashboard}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
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
          {/* Model Selection */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
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
                  <svg
                    className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {modelVersions.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.model_type} - v{model.version.slice(0, 8)} (F1: {model.metrics.f1_score.toFixed(3)}, Accuracy: {model.metrics.accuracy.toFixed(3)})
                    </option>
                  ))}
                </select>
                
                {selectedModelId && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      <strong>Selected Model:</strong>{' '}
                      {modelVersions.find((m) => m.id === selectedModelId)?.model_type}
                    </p>
                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                      Threshold: {modelVersions.find((m) => m.id === selectedModelId)?.classification_threshold.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <svg
                  className="w-5 h-5 text-red-600 dark:text-red-400 mr-2"
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
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: Prediction Form */}
            <div>
              <PredictionForm
                onSubmit={handleFormSubmit}
                isSubmitting={isPredicting}
                disabled={!selectedModelId || modelVersions.length === 0}
              />
            </div>

            {/* Right Column: Prediction Result */}
            <div>
              {prediction ? (
                <PredictionResult
                  prediction={prediction}
                  onReset={handleReset}
                  userRole={user.role}
                />
              ) : (
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 h-full flex items-center justify-center">
                  <div className="text-center text-gray-500 dark:text-gray-400">
                    <svg
                      className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    <p className="text-lg font-medium">No Prediction Yet</p>
                    <p className="text-sm mt-2">
                      Fill out the customer information form and click "Predict Churn" to see results
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Information Panel */}
          <div className="mt-6 bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
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
