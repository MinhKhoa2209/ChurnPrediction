/**
 * Prediction Result Component
 * Displays prediction results including:
 * - Probability gauge with color coding (Req 12.7)
 * - SHAP waterfall chart showing feature contributions (Req 12.8)
 * - Threshold information (Req 12.9, 12.10)
 */

'use client';

import { getProbabilityColor, type PredictionResponse } from '@/lib/predictions';
import ShapWaterfallChart from './shap-waterfall-chart';

interface PredictionResultProps {
  prediction: PredictionResponse;
  onReset: () => void;
  userRole: string;
}

export default function PredictionResult({
  prediction,
  onReset,
  userRole,
}: PredictionResultProps) {
  const probabilityPercent = (prediction.probability * 100).toFixed(1);
  const thresholdPercent = (prediction.threshold * 100).toFixed(0);
  const colors = getProbabilityColor(prediction.probability);

  return (
    <div className="space-y-6">
      {/* Prediction Summary Card */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Prediction Result
          </h2>
          <button
            onClick={onReset}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
          >
            New Prediction
          </button>
        </div>

        {/* Probability Display - Requirement 12.7 */}
        <div className={`${colors.bg} border-2 ${colors.border} rounded-lg p-6 mb-6`}>
          <div className="text-center">
            <div className="mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Churn Probability
              </span>
            </div>
            <div className={`text-6xl font-bold ${colors.text} mb-2`}>
              {probabilityPercent}%
            </div>
            <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold ${colors.text} ${colors.bg} border ${colors.border}`}>
              {colors.label}
            </div>
          </div>

          {/* Prediction Label */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Classification:
              </span>
              <span className={`text-lg font-bold ${
                prediction.prediction === 'Churn' 
                  ? 'text-red-600 dark:text-red-400' 
                  : 'text-green-600 dark:text-green-400'
              }`}>
                {prediction.prediction}
              </span>
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Threshold:
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {thresholdPercent}%
              </span>
            </div>
          </div>
        </div>

        {/* Risk Interpretation */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p className="font-medium mb-1">Recommended Action:</p>
              {prediction.probability < 0.3 ? (
                <p>
                  This customer has a low churn risk. Continue standard engagement and monitor for changes.
                </p>
              ) : prediction.probability < 0.7 ? (
                <p>
                  This customer has a medium churn risk. Consider proactive engagement such as personalized offers or check-in calls.
                </p>
              ) : (
                <p>
                  This customer has a high churn risk. Immediate retention action is recommended, such as dedicated account management or special retention offers.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* SHAP Waterfall Chart - Requirement 12.8 */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Feature Contributions (SHAP Values)
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          This chart shows how each customer feature contributes to the churn prediction.
          Red bars increase churn probability, while green bars decrease it.
        </p>
        <ShapWaterfallChart shapValues={prediction.shap_values} />
      </div>

      {/* Top Contributing Features */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Key Factors
        </h3>
        
        {/* Top Positive Contributors (Increase Churn) */}
        {prediction.shap_values.top_positive.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-3">
              Factors Increasing Churn Risk:
            </h4>
            <div className="space-y-2">
              {prediction.shap_values.top_positive.map((contrib, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {contrib.feature}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Value: {typeof contrib.value === 'number' ? contrib.value.toFixed(2) : contrib.value}
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-sm font-bold text-red-600 dark:text-red-400">
                      +{(contrib.contribution * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Negative Contributors (Decrease Churn) */}
        {prediction.shap_values.top_negative.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-600 dark:text-green-400 mb-3">
              Factors Decreasing Churn Risk:
            </h4>
            <div className="space-y-2">
              {prediction.shap_values.top_negative.map((contrib, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {contrib.feature}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Value: {typeof contrib.value === 'number' ? contrib.value.toFixed(2) : contrib.value}
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="text-sm font-bold text-green-600 dark:text-green-400">
                      {(contrib.contribution * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Prediction Details
        </h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="font-medium text-gray-500 dark:text-gray-400">Prediction ID</dt>
            <dd className="text-gray-900 dark:text-white font-mono text-xs mt-1">
              {prediction.id}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-gray-500 dark:text-gray-400">Model Version ID</dt>
            <dd className="text-gray-900 dark:text-white font-mono text-xs mt-1">
              {prediction.model_version_id.slice(0, 16)}...
            </dd>
          </div>
          <div>
            <dt className="font-medium text-gray-500 dark:text-gray-400">Created At</dt>
            <dd className="text-gray-900 dark:text-white mt-1">
              {new Date(prediction.created_at).toLocaleString()}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-gray-500 dark:text-gray-400">Base Value</dt>
            <dd className="text-gray-900 dark:text-white mt-1">
              {(prediction.shap_values.base_value * 100).toFixed(1)}%
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
