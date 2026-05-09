'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { listModelVersions, type ModelVersionListItem } from '@/lib/models';
import {
  uploadBatchPrediction,
  getBatchPredictionResults,
  downloadBatchPredictionCSV,
  getProbabilityColor,
  type BatchPredictionUploadResponse,
  type BatchPredictionResultsResponse,
  type BatchPredictionResult,
} from '@/lib/predictions';

export default function BatchPredictionPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [modelVersions, setModelVersions] = useState<ModelVersionListItem[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [isLoadingModels, setIsLoadingModels] = useState(true);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [batchData, setBatchData] = useState<BatchPredictionUploadResponse | null>(null);
  const [results, setResults] = useState<BatchPredictionResultsResponse | null>(null);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [isDownloading, setIsDownloading] = useState(false);

  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!token) return;

    const fetchModels = async () => {
      try {
        setIsLoadingModels(true);
        const response = await listModelVersions(token, { status: 'active' });
        setModelVersions(response.versions);
        
        if (response.versions.length > 0) {
          setSelectedModelId(response.versions[0].id);
        }
      } catch (err) {
        console.error('Error loading model versions:', err);
      } finally {
        setIsLoadingModels(false);
      }
    };

    fetchModels();
  }, [token]);

  const handleFileSelect = (file: File) => {
    if (!file.name.endsWith('.csv')) {
      setUploadError('Please select a CSV file');
      return;
    }

    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setUploadError('File size must be less than 50MB');
      return;
    }

    setSelectedFile(file);
    setUploadError(null);
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, []);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedModelId || !token) {
      setUploadError('Please select a file and model version');
      return;
    }

    try {
      setIsUploading(true);
      setUploadError(null);
      setUploadProgress(0);

      const response = await uploadBatchPrediction(
        selectedFile,
        selectedModelId,
        token,
        setUploadProgress
      );

      setBatchData(response);
      
      if (response.status === 'processing' || response.status === 'completed') {
        await loadResults(response.batch_id, 1);
      }
    } catch (err) {
      console.error('Error uploading batch:', err);
      setUploadError(err instanceof Error ? err.message : 'Failed to upload batch');
    } finally {
      setIsUploading(false);
    }
  };

  const loadResults = async (batchId: string, page: number) => {
    if (!token) return;

    try {
      setIsLoadingResults(true);
      const response = await getBatchPredictionResults(batchId, token, page, 50);
      setResults(response);
      setCurrentPage(page);
    } catch (err) {
      console.error('Error loading results:', err);
      setUploadError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setIsLoadingResults(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (batchData) {
      loadResults(batchData.batch_id, newPage);
    }
  };

  const handleDownloadCSV = async () => {
    if (!batchData || !token) return;

    try {
      setIsDownloading(true);
      const blob = await downloadBatchPredictionCSV(batchData.batch_id, token);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_predictions_${batchData.batch_id}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading CSV:', err);
      setUploadError(err instanceof Error ? err.message : 'Failed to download CSV');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    setUploadError(null);
    setBatchData(null);
    setResults(null);
    setCurrentPage(1);
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/predictions')}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 mr-4"
              >
                ← Back to Predictions
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Batch Churn Prediction
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
        <div className="px-4 py-6 sm:px-0 space-y-6">
          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
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
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  No active models available. Please train a model first.
                </p>
              </div>
            ) : (
              <select
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
                disabled={isUploading}
                className="w-full px-4 py-2 border border-gray-300 dark:border-border rounded-lg bg-white dark:bg-muted text-gray-900 dark:text-foreground focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                {modelVersions.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.model_type} - v{model.version.slice(0, 8)} (F1: {model.metrics.f1_score.toFixed(3)})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="bg-white dark:bg-card shadow rounded-lg p-6">
            <h2 className="text-lg font-bold text-gray-900 dark:text-foreground mb-4">
              Upload Customer Data
            </h2>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragging
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-border'
              } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <input
                type="file"
                accept=".csv"
                onChange={handleFileInputChange}
                disabled={isUploading}
                className="hidden"
                id="file-upload"
              />
              
              {selectedFile ? (
                <div className="space-y-2">
                  <svg
                    className="mx-auto h-12 w-12 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="text-sm font-medium text-gray-900 dark:text-foreground">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                  {!isUploading && (
                    <button
                      onClick={() => setSelectedFile(null)}
                      className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ) : (
                <label htmlFor="file-upload" className="cursor-pointer">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="font-medium text-blue-600 dark:text-blue-400">
                      Click to upload
                    </span>{' '}
                    or drag and drop
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    CSV files up to 50MB
                  </p>
                </label>
              )}
            </div>

            {isUploading && (
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300 mb-2">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-muted rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {uploadError && (
              <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-sm text-red-800 dark:text-red-200">{uploadError}</p>
              </div>
            )}

            <div className="mt-6 flex justify-end gap-3">
              {batchData && (
                <button
                  onClick={handleReset}
                  disabled={isUploading}
                  className="px-6 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-muted hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  New Batch
                </button>
              )}
              <button
                onClick={handleUpload}
                disabled={!selectedFile || !selectedModelId || isUploading || modelVersions.length === 0}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-primary-foreground rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Uploading...' : 'Upload and Process'}
              </button>
            </div>
          </div>

          {batchData && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <h2 className="text-lg font-bold text-gray-900 dark:text-foreground mb-4">
                Batch Processing Status
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 dark:bg-muted rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-foreground capitalize">
                    {batchData.status}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-muted rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Records</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-foreground">
                    {batchData.record_count}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-muted rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Processed</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-foreground">
                    {results?.processed_count || 0} / {batchData.record_count}
                  </p>
                </div>
              </div>
            </div>
          )}

          {results && results.results.length > 0 && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900 dark:text-foreground">
                  Prediction Results
                </h2>
                <button
                  onClick={handleDownloadCSV}
                  disabled={isDownloading || batchData?.status !== 'completed'}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-primary-foreground rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {isDownloading ? (
                    <>
                      <svg
                        className="animate-spin h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Downloading...
                    </>
                  ) : (
                    <>
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      Download CSV
                    </>
                  )}
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-border">
                  <thead className="bg-gray-50 dark:bg-muted">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Customer
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Tenure
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Contract
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Monthly Charges
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Probability
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Prediction
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-card divide-y divide-gray-200 dark:divide-border">
                    {results.results.map((result) => {
                      const color = getProbabilityColor(result.probability);
                      return (
                        <tr key={result.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-foreground">
                            {result.input_features.gender}, {result.input_features.SeniorCitizen === 1 ? 'Senior' : 'Non-Senior'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-foreground">
                            {result.input_features.tenure} months
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-foreground">
                            {result.input_features.Contract}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-foreground">
                            ${result.input_features.MonthlyCharges.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color.bg} ${color.text}`}>
                              {(result.probability * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                result.prediction === 'Churn'
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                                  : 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300'
                              }`}
                            >
                              {result.prediction}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {results.total_pages > 1 && (
                <div className="mt-6 flex items-center justify-between border-t border-gray-200 dark:border-border pt-4">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    Showing page {results.page} of {results.total_pages} ({results.total} total results)
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1 || isLoadingResults}
                      className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-muted border border-gray-300 dark:border-border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    
                    <div className="flex gap-1">
                      {Array.from({ length: Math.min(5, results.total_pages) }, (_, i) => {
                        let pageNum;
                        if (results.total_pages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= results.total_pages - 2) {
                          pageNum = results.total_pages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        
                        return (
                          <button
                            key={pageNum}
                            onClick={() => handlePageChange(pageNum)}
                            disabled={isLoadingResults}
                            className={`px-3 py-2 text-sm font-medium rounded-lg ${
                              currentPage === pageNum
                                ? 'bg-blue-600 text-primary-foreground'
                                : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-muted border border-gray-300 dark:border-border hover:bg-gray-50 dark:hover:bg-gray-600'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === results.total_pages || isLoadingResults}
                      className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-muted border border-gray-300 dark:border-border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {!batchData && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-12 text-center">
              <svg
                className="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 dark:text-foreground mb-2">
                No Batch Uploaded
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Upload a CSV file with customer data to generate batch predictions
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
