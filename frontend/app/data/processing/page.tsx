'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { useDatasetStore } from '@/lib/store/dataset-store';
import { Activity, CheckCircle, Clock, Database, ArrowRight } from 'lucide-react';

export default function DataProcessingPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();
  const { currentDataset } = useDatasetStore();
  
  const [activeTab, setActiveTab] = useState<'overview' | 'cleaning' | 'transformation'>('overview');

  useEffect(() => {
    if (!authLoading && (!user || user.role !== 'Admin')) {
      router.push('/dashboard');
    }
  }, [user, authLoading, router]);

  if (authLoading || (!user || user.role !== 'Admin')) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Data Processing pipeline
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          
          {/* Status Header */}
          <div className="bg-white dark:bg-card shadow rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground">Dataset Processing</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {currentDataset ? `Processing dataset ID: ${currentDataset.id}` : 'No active dataset selected for processing'}
              </p>
            </div>
            <div className="flex gap-3">
              <button 
                onClick={() => router.push('/data/upload')}
                className="px-4 py-2 border border-gray-300 dark:border-border rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-muted transition-colors"
              >
                Upload New Data
              </button>
              <button 
                onClick={() => router.push('/data/eda')}
                disabled={!currentDataset}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                Continue to EDA <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Sidebar Navigation */}
            <div className="md:col-span-1 space-y-2">
              <button 
                onClick={() => setActiveTab('overview')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'overview' 
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-muted'
                }`}
              >
                Processing Overview
              </button>
              <button 
                onClick={() => setActiveTab('cleaning')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'cleaning' 
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-muted'
                }`}
              >
                Data Cleaning
              </button>
              <button 
                onClick={() => setActiveTab('transformation')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'transformation' 
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-muted'
                }`}
              >
                Feature Transformation
              </button>
            </div>

            {/* Main Content Area */}
            <div className="md:col-span-3">
              <div className="bg-white dark:bg-card shadow rounded-lg p-6 min-h-[400px]">
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-foreground border-b pb-2">Pipeline Status</h3>
                    
                    {!currentDataset ? (
                      <div className="text-center py-12">
                        <Database className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-500">Please upload a dataset first to view processing details.</p>
                      </div>
                    ) : (
                      <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-300 dark:before:via-gray-600 before:to-transparent">
                        
                        {/* Step 1 */}
                        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                          <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-card bg-green-500 text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            <CheckCircle className="w-5 h-5" />
                          </div>
                          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg bg-gray-50 dark:bg-muted border border-gray-100 dark:border-border shadow-sm">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-bold text-gray-900 dark:text-foreground">Upload & Validation</h4>
                              <span className="text-xs font-medium text-green-600">Completed</span>
                            </div>
                            <p className="text-sm text-gray-500">File uploaded and schema validated successfully.</p>
                          </div>
                        </div>

                        {/* Step 2 */}
                        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                          <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-card bg-blue-500 text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            <Activity className="w-5 h-5 animate-pulse" />
                          </div>
                          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 shadow-sm">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-bold text-gray-900 dark:text-foreground">Data Cleaning</h4>
                              <span className="text-xs font-medium text-blue-600 dark:text-blue-400">Processing</span>
                            </div>
                            <p className="text-sm text-gray-500">Handling missing values and outliers.</p>
                          </div>
                        </div>

                        {/* Step 3 */}
                        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                          <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-card bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            <Clock className="w-5 h-5" />
                          </div>
                          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg bg-white dark:bg-card border border-gray-100 dark:border-border opacity-60">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-bold text-gray-900 dark:text-foreground">Feature Engineering</h4>
                              <span className="text-xs font-medium text-gray-500">Pending</span>
                            </div>
                            <p className="text-sm text-gray-500">Creating derived features and encoding.</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {activeTab === 'cleaning' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-foreground border-b pb-2">Data Cleaning Log</h3>
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                      <p>Initializing cleaning pipeline...</p>
                      <p className="text-gray-500">Waiting for dataset upload to start detailed cleaning...</p>
                    </div>
                  </div>
                )}

                {activeTab === 'transformation' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-foreground border-b pb-2">Feature Transformation Log</h3>
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                      <p>Pipeline ready...</p>
                      <p className="text-gray-500">Transformations will appear here once cleaning is complete.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
