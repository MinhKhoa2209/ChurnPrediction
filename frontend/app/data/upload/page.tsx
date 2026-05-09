'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { useDatasetStore, Dataset } from '@/lib/store/dataset-store';
import { FileUpload } from '@/components/data';
import { api } from '@/lib/api';

export default function DataUploadPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();
  const {
    currentDataset,
    isUploading,
    uploadProgress,
    uploadError,
    setCurrentDataset,
    setUploading,
    setUploadProgress,
    setUploadError,
    resetUpload,
    addDataset,
  } = useDatasetStore();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile || !token) return;

    try {
      setUploading(true);
      setUploadError(null);
      setUploadProgress(0);

    const response = await api.upload<Dataset>(
        '/datasets/upload',
        selectedFile,
        token,
        (progress) => {
          setUploadProgress(progress);
        }
      );

    addDataset(response);
    setCurrentDataset(response);

    setSelectedFile(null);
    setUploadProgress(100);

    setTimeout(() => {
      resetUpload();
    }, 2000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadError(errorMessage);
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    resetUpload();
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

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

  const canUpload = user.role === 'Admin' || user.role === 'Data_Scientist';

  if (!canUpload) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-background">
        <nav className="bg-white dark:bg-card shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                  Data Upload
                </h1>
              </div>
              <div className="flex items-center">
                <button
                  onClick={handleBackToDashboard}
                  className="text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-primary-foreground"
                >
                  Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                Access Denied
              </h2>
              <p className="text-sm text-red-700 dark:text-red-300">
                You do not have permission to upload data. This feature requires Data_Scientist or Admin role.
              </p>
            </div>
          </div>
        </main>
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
                Upload Customer Data
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {user.email} ({user.role})
              </span>
              <button
                onClick={handleBackToDashboard}
                className="text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-primary-foreground"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground mb-6">
              Upload Dataset
            </h2>

            <div className="space-y-6">
              <FileUpload
                onFileSelect={handleFileSelect}
                maxSizeMB={50}
                disabled={isUploading}
              />

              {selectedFile && !isUploading && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        Selected File
                      </p>
                      <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                        {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                      </p>
                    </div>
                    <button
                      onClick={handleCancel}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}

              {isUploading && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Uploading...
                    </span>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {uploadProgress}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-muted rounded-full h-2.5">
                    <div
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  {selectedFile && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {selectedFile.name}
                    </p>
                  )}
                </div>
              )}

              {uploadError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-red-400"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                        Upload Failed
                      </h3>
                      <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                        <p>{uploadError}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {currentDataset && !isUploading && !uploadError && uploadProgress === 100 && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-green-400"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                        Upload Successful
                      </h3>
                      <div className="mt-2 text-sm text-green-700 dark:text-green-300">
                        <p>{currentDataset.message}</p>
                        <p className="mt-1">
                          Dataset ID: <span className="font-mono">{currentDataset.id}</span>
                        </p>
                        <p>Status: {currentDataset.status}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  onClick={handleCancel}
                  disabled={isUploading}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-muted border border-gray-300 dark:border-border rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading}
                  className="px-4 py-2 text-sm font-medium text-primary-foreground bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? 'Uploading...' : 'Upload Dataset'}
                </button>
              </div>
            </div>
          </div>

          <div className="mt-6 bg-white dark:bg-card shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-4">
              Dataset Requirements
            </h3>
            <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
              <div>
                <p className="font-medium">File Format:</p>
                <p className="text-gray-600 dark:text-gray-400">CSV (Comma-Separated Values)</p>
              </div>
              <div>
                <p className="font-medium">Maximum File Size:</p>
                <p className="text-gray-600 dark:text-gray-400">50 MB</p>
              </div>
              <div>
                <p className="font-medium">Required Columns:</p>
                <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 mt-1 space-y-1">
                  <li>customerID, gender, SeniorCitizen, Partner, Dependents</li>
                  <li>tenure, PhoneService, MultipleLines, InternetService</li>
                  <li>OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport</li>
                  <li>StreamingTV, StreamingMovies, Contract, PaperlessBilling</li>
                  <li>PaymentMethod, MonthlyCharges, TotalCharges, Churn</li>
                </ul>
              </div>
              <div>
                <p className="font-medium">Processing:</p>
                <p className="text-gray-600 dark:text-gray-400">
                  Files are validated immediately and processed in the background. You will be notified when processing is complete.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
