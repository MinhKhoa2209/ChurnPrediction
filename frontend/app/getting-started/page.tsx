'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { 
  BookOpen,
  CheckCircle,
  ChevronRight,
  ArrowLeft,
  Brain,
  Target,
  BarChart3,
  Upload,
  LineChart,
  FileText,
  History,
  Bell,
  Users,
  TrendingUp,
} from 'lucide-react';

export default function GettingStartedPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const userRole = user?.role || 'Analyst';

  const analystSteps = [
    {
      number: 1,
      title: 'View Available Models',
      description: 'Browse trained models that are ready for predictions.',
      details: [
        'Navigate to the Models page',
        'Review available trained models',
        'Check model accuracy and performance metrics',
        'Select the best model for your predictions',
      ],
      action: {
        label: 'View Models',
        path: '/models',
      },
      icon: Brain,
      color: 'purple',
    },
    {
      number: 2,
      title: 'Make Single Predictions',
      description: 'Predict churn for individual customers.',
      details: [
        'Enter customer data manually',
        'Select a trained model version',
        'View churn probability scores',
        'Understand feature contributions with SHAP values',
      ],
      action: {
        label: 'Single Prediction',
        path: '/predictions/single',
      },
      icon: Target,
      color: 'blue',
    },
    {
      number: 3,
      title: 'Batch Predictions',
      description: 'Upload CSV files for bulk predictions.',
      details: [
        'Prepare CSV file with customer data',
        'Upload file for batch processing',
        'Monitor prediction progress',
        'Download results when complete',
      ],
      action: {
        label: 'Batch Predictions',
        path: '/predictions/batch',
      },
      icon: BarChart3,
      color: 'green',
    },
    {
      number: 4,
      title: 'View Prediction History',
      description: 'Review past predictions and their results.',
      details: [
        'Access prediction history',
        'Filter by date and model',
        'Export prediction results',
        'Track prediction accuracy over time',
      ],
      action: {
        label: 'View History',
        path: '/predictions',
      },
      icon: History,
      color: 'indigo',
    },
    {
      number: 5,
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
      icon: FileText,
      color: 'amber',
    },
    {
      number: 6,
      title: 'Manage Notifications',
      description: 'Stay updated with system notifications.',
      details: [
        'View prediction completion alerts',
        'Check model availability notifications',
        'Configure notification preferences',
        'Mark notifications as read',
      ],
      action: {
        label: 'Notifications',
        path: '/notifications',
      },
      icon: Bell,
      color: 'pink',
    },
  ];

  const adminSteps = [
    {
      number: 1,
      title: 'Upload Customer Data',
      description: 'Upload and manage customer datasets for analysis.',
      details: [
        'Navigate to the Data Upload page',
        'Select a CSV file (up to 50MB)',
        'Ensure your file contains all required columns',
        'Wait for validation and processing to complete',
      ],
      action: {
        label: 'Upload Data',
        path: '/data/upload',
      },
      icon: Upload,
      color: 'blue',
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
      icon: LineChart,
      color: 'green',
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
        path: '/models/training',
      },
      icon: Brain,
      color: 'purple',
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
      icon: TrendingUp,
      color: 'indigo',
    },
    {
      number: 5,
      title: 'Make Predictions',
      description: 'Use your trained models to predict customer churn.',
      details: [
        'Enter customer data for single predictions',
        'Upload CSV files for batch predictions',
        'View churn probability scores',
        'Access prediction history and analytics',
      ],
      action: {
        label: 'Make Predictions',
        path: '/predictions/single',
      },
      icon: Target,
      color: 'pink',
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
      icon: FileText,
      color: 'amber',
    },
  ];

  const steps = userRole === 'Admin' ? adminSteps : analystSteps;

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string; border: string; hover: string }> = {
      blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-800', hover: 'hover:bg-blue-100 dark:hover:bg-blue-900/30' },
      green: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', border: 'border-green-200 dark:border-green-800', hover: 'hover:bg-green-100 dark:hover:bg-green-900/30' },
      purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', border: 'border-purple-200 dark:border-purple-800', hover: 'hover:bg-purple-100 dark:hover:bg-purple-900/30' },
      indigo: { bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-600 dark:text-indigo-400', border: 'border-indigo-200 dark:border-indigo-800', hover: 'hover:bg-indigo-100 dark:hover:bg-indigo-900/30' },
      pink: { bg: 'bg-pink-50 dark:bg-pink-900/20', text: 'text-pink-600 dark:text-pink-400', border: 'border-pink-200 dark:border-pink-800', hover: 'hover:bg-pink-100 dark:hover:bg-pink-900/30' },
      amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800', hover: 'hover:bg-amber-100 dark:hover:bg-amber-900/30' },
    };
    return colors[color] || colors.blue;
  };

  return (
    <>
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
            <BookOpen className="w-6 h-6 text-white" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
              Getting Started Guide
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-muted-foreground">
                Role-specific guide for
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                {userRole}
              </span>
            </div>
          </div>
        </div>
        <p className="text-lg text-muted-foreground">
          {userRole === 'Admin' 
            ? 'Complete guide to managing and overseeing the platform' 
            : 'Follow these steps to start predicting customer churn'}
        </p>
      </div>

      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-xl p-6 mb-8 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            {userRole === 'Admin' ? (
              <Users className="w-12 h-12 text-blue-600 dark:text-blue-400" />
            ) : (
              <Target className="w-12 h-12 text-purple-600 dark:text-purple-400" />
            )}
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground mb-2">
              {userRole === 'Admin' 
                ? 'Welcome, Administrator!' 
                : 'Welcome to the Customer Churn Prediction Platform'}
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              {userRole === 'Admin'
                ? 'As an administrator, you have full access to upload data, train models, make predictions, and generate reports. Use this guide to understand the complete workflow from data upload to insights generation.'
                : 'As an analyst, you can make predictions using trained models and generate reports. Administrators handle data uploads and model training. Use this guide to understand how to work with available models.'}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {steps.map((step) => {
          const colors = getColorClasses(step.color);
          const IconComponent = step.icon;
          
          return (
            <div
              key={step.number}
              className={`bg-card shadow-md rounded-xl p-6 border-2 ${colors.border} transition-all hover:shadow-xl hover:scale-[1.02]`}
            >
              <div className="flex items-start space-x-5">
                <div className="shrink-0">
                  <div className={`flex items-center justify-center w-14 h-14 rounded-xl ${colors.bg} shadow-md`}>
                    <IconComponent className={`w-7 h-7 ${colors.text}`} />
                  </div>
                  <div className={`text-center mt-2 text-sm font-bold ${colors.text}`}>
                    Step {step.number}
                  </div>
                </div>

                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-foreground mb-2">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground mb-4 text-base">
                    {step.description}
                  </p>

                  <ul className="space-y-2.5 mb-5">
                    {step.details.map((detail, index) => (
                      <li
                        key={index}
                        className="flex items-start text-foreground/90"
                      >
                        <CheckCircle
                          className={`w-5 h-5 ${colors.text} mr-3 mt-0.5 shrink-0`}
                          aria-hidden="true"
                        />
                        <span className="leading-relaxed">{detail}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => router.push(step.action.path)}
                    className={`inline-flex items-center px-5 py-2.5 ${colors.bg} ${colors.hover} ${colors.text} rounded-lg font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-ring shadow-sm hover:shadow-md`}
                  >
                    {step.action.label}
                    <ChevronRight className="w-4 h-4 ml-2" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 text-center">
        <button
          onClick={() => router.push('/dashboard')}
          className="inline-flex items-center px-8 py-3 bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <ArrowLeft className="w-5 h-5 mr-2" aria-hidden="true" />
          Back to Dashboard
        </button>
      </div>
    </>
  );
}
