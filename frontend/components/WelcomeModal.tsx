/**
 * Welcome Modal Component
 * Shows onboarding guide for new users on first visit

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

const WELCOME_MODAL_KEY = 'churn-platform-welcome-shown';

interface WelcomeModalProps {
  onClose?: () => void;
}

export function WelcomeModal({ onClose }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();

  useEffect(() => {
    // Check if user has seen the welcome modal before
    const hasSeenWelcome = localStorage.getItem(WELCOME_MODAL_KEY);
    if (!hasSeenWelcome) {
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    // Mark welcome modal as shown
    localStorage.setItem(WELCOME_MODAL_KEY, 'true');
    setIsOpen(false);
    onClose?.();
  };

  const handleGetStarted = () => {
    handleClose();
    // Navigate to data upload page
    router.push('/data/upload');
  };

  const handleViewGuide = () => {
    handleClose();
    // Navigate to getting started guide
    router.push('/getting-started');
  };

  const steps = [
    {
      title: 'Upload Data',
      description: 'Start by uploading your customer data in CSV format. The platform supports files up to 50MB.',
      icon: (
        <svg
          className="w-12 h-12 text-blue-600 dark:text-blue-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      ),
    },
    {
      title: 'Train Models',
      description: 'Train multiple machine learning models on your data. The platform automatically handles preprocessing and optimization.',
      icon: (
        <svg
          className="w-12 h-12 text-green-600 dark:text-green-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
          />
        </svg>
      ),
    },
    {
      title: 'Make Predictions',
      description: 'Use trained models to predict customer churn. Get probability scores and insights to take proactive action.',
      icon: (
        <svg
          className="w-12 h-12 text-purple-600 dark:text-purple-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      ),
    },
  ];

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-modal-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Close button */}
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label="Close welcome modal"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>

          {/* Header */}
          <div className="text-center mb-8">
            <h2
              id="welcome-modal-title"
              className="text-3xl font-bold text-gray-900 dark:text-white mb-2"
            >
              Welcome to Churn Prediction Platform
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Get started in 3 simple steps
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-6 mb-8">
            {steps.map((step, index) => (
              <div
                key={index}
                className={`flex items-start space-x-4 p-4 rounded-lg transition-colors ${
                  currentStep === index
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                    : 'bg-gray-50 dark:bg-gray-700/50'
                }`}
              >
                {/* Step number and icon */}
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-16 h-16 rounded-full bg-white dark:bg-gray-800 shadow-md">
                    {step.icon}
                  </div>
                  <div className="text-center mt-2">
                    <span className="text-sm font-semibold text-gray-600 dark:text-gray-400">
                      Step {index + 1}
                    </span>
                  </div>
                </div>

                {/* Step content */}
                <div className="flex-1 pt-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Step indicators */}
          <div className="flex justify-center space-x-2 mb-6">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={`w-3 h-3 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  currentStep === index
                    ? 'bg-blue-600'
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
                aria-label={`Go to step ${index + 1}`}
                aria-current={currentStep === index ? 'step' : undefined}
              />
            ))}
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center">
            <div className="flex space-x-3">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              >
                Skip for now
              </button>
              <button
                onClick={handleViewGuide}
                className="px-4 py-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              >
                View Full Guide
              </button>
            </div>

            <div className="flex space-x-3">
              {currentStep > 0 && (
                <button
                  onClick={() => setCurrentStep(currentStep - 1)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Previous
                </button>
              )}

              {currentStep < steps.length - 1 ? (
                <button
                  onClick={() => setCurrentStep(currentStep + 1)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleGetStarted}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
                >
                  Get Started
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
