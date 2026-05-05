/**
 * Getting Started Guide Page
 * Comprehensive guide for new users

'use client';

import { Navigation } from '@/components/Navigation';
import { useRouter } from 'next/navigation';

export default function GettingStartedPage() {
  const router = useRouter();

  const steps = [
    {
      number: 1,
      title: 'Upload Your Customer Data',
      description: 'Start by uploading your customer data in CSV format.',
      details: [
        'Navigate to the Data Upload page',
        'Select a CSV file (up to 50MB)',
        'Ensure your file contains all required columns',
        'Wait for validation and processing to complete',
      ],
      action: {
        label: 'Go to Upload',
        path: '/data/upload',
      },
    },
    {
      number: 2,
      title: 'Explore Your Data',
      description: 'Understand your data through visualizations and statistics.',
      details: [
        'View correlation heatmaps',
        'Analyze distribution histograms',
        'Examine churn rates by different features',
        'Identify patterns and outliers',
      ],
      action: {
        label: 'Explore Data',
        path: '/data/eda',
      },
    },
    {
      number: 3,
      title: 'Train Machine Learning Models',
      description: 'Train multiple models to find the best predictor.',
      details: [
        'Select model types (KNN, Naive Bayes, Decision Tree, SVM)',
        'Enable hyperparameter optimization for better accuracy',
        'Monitor training progress in real-time',
        'Review evaluation metrics when complete',
      ],
      action: {
        label: 'Train Models',
        path: '/models/train',
      },
    },
    {
      number: 4,
      title: 'Compare Model Performance',
      description: 'Evaluate and compare trained models side-by-side.',
      details: [
        'View accuracy, precision, recall, and F1-score',
        'Examine confusion matrices',
        'Compare ROC curves',
        'Select the best performing model',
      ],
      action: {
        label: 'Compare Models',
        path: '/models/comparison',
      },
    },
    {
      number: 5,
      title: 'Make Predictions',
      description: 'Use your trained models to predict customer churn.',
      details: [
        'Enter customer data for single predictions',
        'Upload CSV files for batch predictions',
        'View churn probability scores',
        'Understand feature contributions with SHAP values',
      ],
      action: {
        label: 'Make Predictions',
        path: '/predictions/single',
      },
    },
    {
      number: 6,
      title: 'Generate Reports',
      description: 'Create comprehensive reports to share insights.',
      details: [
        'Generate PDF reports with metrics and visualizations',
        'Export prediction results as CSV',
        'Share insights with stakeholders',
        'Track model performance over time',
      ],
      action: {
        label: 'Generate Reports',
        path: '/reports',
      },
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />

      <main className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Getting Started Guide
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Follow these steps to start predicting customer churn
          </p>
        </div>

        {/* Introduction */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-blue-900 dark:text-blue-100 mb-2">
            Welcome to the Customer Churn Prediction Platform
          </h2>
          <p className="text-blue-800 dark:text-blue-200">
            This platform helps you identify customers at risk of churning using machine learning.
            Follow the steps below to get started with your first prediction model.
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-6">
          {steps.map((step) => (
            <div
              key={step.number}
              className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-start space-x-4">
                {/* Step number */}
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-600 text-white text-xl font-bold">
                    {step.number}
                  </div>
                </div>

                {/* Step content */}
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    {step.description}
                  </p>

                  {/* Details list */}
                  <ul className="space-y-2 mb-4">
                    {step.details.map((detail, index) => (
                      <li
                        key={index}
                        className="flex items-start text-gray-700 dark:text-gray-300"
                      >
                        <svg
                          className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          aria-hidden="true"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        {detail}
                      </li>
                    ))}
                  </ul>

                  {/* Action button */}
                  <button
                    onClick={() => router.push(step.action.path)}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {step.action.label}
                    <svg
                      className="w-4 h-4 ml-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Resources */}
        <div className="mt-8 bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Additional Resources
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start space-x-3">
              <svg
                className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Documentation
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Detailed guides and API references
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <svg
                className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Support
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Get help from our support team
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <svg
                className="w-6 h-6 text-purple-600 dark:text-purple-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Video Tutorials
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Watch step-by-step video guides
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <svg
                className="w-6 h-6 text-orange-600 dark:text-orange-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  Community Forum
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Connect with other users
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Back to Dashboard */}
        <div className="mt-8 text-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="inline-flex items-center px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Dashboard
          </button>
        </div>
      </main>
    </div>
  );
}
