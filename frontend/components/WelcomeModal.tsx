'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { X, Zap, Cpu, BarChart3, CloudUpload, BrainCircuit, ChevronLeft, ChevronRight, Rocket, BookOpen, FileText } from 'lucide-react';

const WELCOME_MODAL_KEY = 'churn-platform-welcome-shown';

interface WelcomeModalProps {
  onClose?: () => void;
  userRole?: 'Admin' | 'Analyst';
}

export function WelcomeModal({ onClose, userRole = 'Analyst' }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const hasSeenWelcome = localStorage.getItem(WELCOME_MODAL_KEY);
    if (!hasSeenWelcome) {
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    localStorage.setItem(WELCOME_MODAL_KEY, 'true');
    setIsOpen(false);
    onClose?.();
  };

  const handleGetStarted = () => {
    handleClose();
    router.push(userRole === 'Admin' ? '/data/upload' : '/predictions/single');
  };

  const handleViewGuide = () => {
    handleClose();
    router.push('/getting-started');
  };

  const analystSteps = [
    {
      title: 'View Models',
      description: 'Browse available trained models and check their performance metrics.',
      icon: <Cpu className="w-12 h-12 text-purple-600 dark:text-purple-400" />,
    },
    {
      title: 'Make Predictions',
      description: 'Use trained models to predict customer churn with single or batch predictions.',
      icon: <BarChart3 className="w-12 h-12 text-blue-600 dark:text-blue-400" />,
    },
    {
      title: 'Generate Reports',
      description: 'Create comprehensive reports and export prediction results for analysis.',
      icon: <FileText className="w-12 h-12 text-green-600 dark:text-green-400" />,
    },
  ];

  const adminSteps = [
    {
      title: 'Upload Data',
      description: 'Start by uploading customer data in CSV format for analysis and model training.',
      icon: <CloudUpload className="w-12 h-12 text-blue-600 dark:text-blue-400" />,
    },
    {
      title: 'Train Models',
      description: 'Train multiple machine learning models with automatic preprocessing and optimization.',
      icon: <BrainCircuit className="w-12 h-12 text-green-600 dark:text-green-400" />,
    },
    {
      title: 'Make Predictions',
      description: 'Use trained models to predict customer churn and generate actionable insights.',
      icon: <BarChart3 className="w-12 h-12 text-purple-600 dark:text-purple-400" />,
    },
  ];

  const steps = userRole === 'Admin' ? adminSteps : analystSteps;

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
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-card rounded-2xl shadow-2xl max-w-3xl w-full p-8 border border-gray-200 dark:border-border">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg p-1 transition-colors"
            aria-label="Close welcome modal"
          >
            <X className="w-6 h-6" aria-hidden="true" />
          </button>

          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
              <Zap className="w-8 h-8 text-white" aria-hidden="true" />
            </div>
            <h2
              id="welcome-modal-title"
              className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent mb-3"
            >
              Welcome to Churn Prediction Platform
            </h2>
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              {userRole === 'Admin' 
                ? 'Complete workflow from data to insights' 
                : 'Work with trained models to generate predictions'}
            </p>
            <div className="inline-flex items-center gap-2 mt-3 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-full">
              <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                Role: {userRole}
              </span>
            </div>
          </div>

          <div className="space-y-5 mb-10">
            {steps.map((step, index) => (
              <div
                key={index}
                className={`flex items-start space-x-5 p-5 rounded-xl transition-all duration-300 cursor-pointer ${
                  currentStep === index
                    ? 'bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-blue-500 shadow-lg scale-105'
                    : 'bg-gray-50 dark:bg-muted/50 border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                }`}
                onClick={() => setCurrentStep(index)}
              >
                <div className="flex-shrink-0">
                  <div className={`flex items-center justify-center w-16 h-16 rounded-xl shadow-md transition-all ${
                    currentStep === index
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 scale-110'
                      : 'bg-white dark:bg-card'
                  }`}>
                    {currentStep === index ? (
                      <div className="text-white">
                        {step.icon}
                      </div>
                    ) : (
                      step.icon
                    )}
                  </div>
                  <div className="text-center mt-2">
                    <span className={`text-sm font-bold ${
                      currentStep === index
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      Step {index + 1}
                    </span>
                  </div>
                </div>

                <div className="flex-1 pt-1">
                  <h3 className={`text-xl font-bold mb-2 ${
                    currentStep === index
                      ? 'text-blue-900 dark:text-blue-100'
                      : 'text-gray-900 dark:text-foreground'
                  }`}>
                    {step.title}
                  </h3>
                  <p className={`text-sm leading-relaxed ${
                    currentStep === index
                      ? 'text-gray-700 dark:text-gray-300'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}>
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center space-x-2 mb-8">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={`h-2 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  currentStep === index
                    ? 'w-8 bg-gradient-to-r from-blue-600 to-purple-600'
                    : 'w-2 bg-gray-300 dark:bg-muted hover:bg-gray-400'
                }`}
                aria-label={`Go to step ${index + 1}`}
                aria-current={currentStep === index ? 'step' : undefined}
              />
            ))}
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t border-gray-200 dark:border-border">
            <div className="flex flex-wrap justify-center sm:justify-start gap-3">
              <button
                onClick={handleClose}
                className="px-5 py-2.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 font-medium rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Skip for now
              </button>
              <button
                onClick={handleViewGuide}
                className="px-5 py-2.5 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <span className="inline-flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4" /> View Full Guide
                </span>
              </button>
            </div>

            <div className="flex gap-3">
              {currentStep > 0 && (
                <button
                  onClick={() => setCurrentStep(currentStep - 1)}
                  className="px-5 py-2.5 border-2 border-gray-300 dark:border-border text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 inline-flex items-center gap-1"
                >
                  <ChevronLeft className="w-4 h-4" /> Previous
                </button>
              )}

              {currentStep < steps.length - 1 ? (
                <button
                  onClick={() => setCurrentStep(currentStep + 1)}
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 inline-flex items-center gap-1"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleGetStarted}
                  className="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 animate-pulse inline-flex items-center gap-1.5"
                >
                  <Rocket className="w-4 h-4" /> Get Started
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
