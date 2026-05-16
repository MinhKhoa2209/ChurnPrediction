'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { listDatasets, type Dataset } from '@/lib/datasets';
import { createTrainingJob, listTrainingJobs, type TrainingJob } from '@/lib/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, CheckCircle2, Clock, XCircle, Loader2, BrainCircuit } from 'lucide-react';

const MODEL_TYPES = [
  { id: 'KNN', name: 'K-Nearest Neighbors', description: 'Fast and simple classification algorithm' },
  { id: 'NaiveBayes', name: 'Naive Bayes', description: 'Probabilistic classifier based on Bayes theorem' },
  { id: 'DecisionTree', name: 'Decision Tree', description: 'Tree-based model with interpretable rules' },
  { id: 'SVM', name: 'Support Vector Machine', description: 'Powerful classifier for complex patterns' },
];

export default function TrainingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, token, isLoading: authLoading } = useAuthStore();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([]);
  const [activeJobIds, setActiveJobIds] = useState<string[]>([]);
  const [showProgress, setShowProgress] = useState(false);

  // Load datasets
  useEffect(() => {
    const fetchDatasets = async () => {
      if (!token) return;

      try {
        setLoading(true);
        const data = await listDatasets(token);
        const readyDatasets = data.datasets.filter(d => d.status === 'ready');
        setDatasets(readyDatasets);

        // Auto-select dataset from query params
        const datasetId = searchParams.get('dataset');
        if (datasetId && readyDatasets.some(d => d.id === datasetId)) {
          setSelectedDataset(datasetId);
        } else if (readyDatasets.length === 1) {
          setSelectedDataset(readyDatasets[0].id);
        }
      } catch (err) {
        console.error('Error loading datasets:', err);
        setError(err instanceof Error ? err.message : 'Failed to load datasets');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchDatasets();
    }
  }, [token, searchParams]);

  // Poll training jobs when showing progress
  useEffect(() => {
    if (!showProgress || !token) return;

    const pollJobs = async () => {
      try {
        const response = await listTrainingJobs(token);
        const visibleJobs =
          activeJobIds.length > 0
            ? response.jobs.filter((job) => activeJobIds.includes(job.id))
            : response.jobs;

        setTrainingJobs(visibleJobs);

        // Check if all jobs are completed or failed
        const allDone = visibleJobs.length > 0 && visibleJobs.every(
          job => job.status === 'completed' || job.status === 'failed'
        );

        if (allDone) {
          // Stop polling after a delay to show final state
          setTimeout(() => {
            setShowProgress(false);
          }, 3000);
        }
      } catch (err) {
        console.error('Error polling training jobs:', err);
      }
    };

    pollJobs();
    const interval = setInterval(pollJobs, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [activeJobIds, showProgress, token]);

  const handleModelToggle = (modelId: string) => {
    setSelectedModels(prev =>
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  const handleStartTraining = async () => {
    if (!token || !selectedDataset || selectedModels.length === 0) return;

    try {
      setSubmitting(true);
      setError(null);

      const response = await createTrainingJob(
        {
          dataset_id: selectedDataset,
          model_types: selectedModels,
        },
        token
      );

      setActiveJobIds(response.jobs.map((job) => job.id));
      setTrainingJobs(response.jobs);
      setShowProgress(true);
    } catch (err) {
      console.error('Error starting training:', err);
      setError(err instanceof Error ? err.message : 'Failed to start training');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-600 dark:text-blue-400 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200';
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200';
      default:
        return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-200';
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (user.role !== 'Admin') {
    return (
      <div className="min-h-screen bg-background p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You do not have permission to train models. This feature requires the Admin role.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
              <BrainCircuit className="h-8 w-8 text-primary" />
              Train Models
            </h1>
            <p className="text-muted-foreground mt-1">
              Select a dataset and model types to start training
            </p>
          </div>
          <Button variant="outline" onClick={() => router.push('/models/comparison')}>
            View Models
          </Button>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {!showProgress ? (
          <>
            {/* Dataset Selection */}
            <Card>
              <CardHeader>
                <CardTitle>1. Select Dataset</CardTitle>
              </CardHeader>
              <CardContent>
                {datasets.length === 0 ? (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      No datasets available. Please upload a dataset first.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="space-y-2">
                    {datasets.map((dataset) => (
                      <div
                        key={dataset.id}
                        onClick={() => setSelectedDataset(dataset.id)}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          selectedDataset === dataset.id
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-foreground">{dataset.filename}</p>
                            <p className="text-sm text-muted-foreground">
                              {dataset.record_count} records • Uploaded{' '}
                              {new Date(dataset.uploaded_at).toLocaleDateString()}
                            </p>
                          </div>
                          {selectedDataset === dataset.id && (
                            <CheckCircle2 className="h-5 w-5 text-primary" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Model Selection */}
            <Card>
              <CardHeader>
                <CardTitle>2. Select Model Types</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {MODEL_TYPES.map((model) => (
                    <div
                      key={model.id}
                      onClick={() => handleModelToggle(model.id)}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedModels.includes(model.id)
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <Checkbox
                          checked={selectedModels.includes(model.id)}
                          onCheckedChange={() => handleModelToggle(model.id)}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <p className="font-medium text-foreground">{model.name}</p>
                          <p className="text-sm text-muted-foreground">{model.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {selectedModels.length > 0 && (
                  <p className="text-sm text-muted-foreground mt-4">
                    {selectedModels.length} model{selectedModels.length > 1 ? 's' : ''} selected
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Training Info */}
            <Card>
              <CardHeader>
                <CardTitle>Training Process</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <p>Data preprocessing (imputation, encoding, scaling, SMOTE)</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <p>Hyperparameter optimization for best performance</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <p>Model evaluation with multiple metrics</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <p>Automatic model versioning and artifact storage</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Start Training Button */}
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => router.push('/dashboard')}>
                Cancel
              </Button>
              <Button
                onClick={handleStartTraining}
                disabled={!selectedDataset || selectedModels.length === 0 || submitting}
                className="min-w-[150px]"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Starting...
                  </>
                ) : (
                  'Start Training'
                )}
              </Button>
            </div>
          </>
        ) : (
          /* Training Progress */
          <Card>
            <CardHeader>
              <CardTitle>Training Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {trainingJobs.length === 0 ? (
                <div className="text-center py-8">
                  <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
                  <p className="text-muted-foreground">Initializing training jobs...</p>
                </div>
              ) : (
                trainingJobs.map((job) => (
                  <div key={job.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(job.status)}
                        <div>
                          <p className="font-medium text-foreground">{job.model_type}</p>
                          <p className="text-sm text-muted-foreground">
                            {job.status === 'completed' && 'Training completed successfully'}
                            {job.status === 'failed' && `Failed: ${job.error_message || 'Unknown error'}`}
                            {job.status === 'running' && 'Training in progress...'}
                            {job.status === 'queued' && 'Waiting to start...'}
                          </p>
                          {job.current_iteration !== null && job.total_iterations !== null && (
                            <p className="text-xs text-muted-foreground">
                              Optimization progress: {job.current_iteration}/{job.total_iterations}
                            </p>
                          )}
                        </div>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          job.status
                        )}`}
                      >
                        {job.status}
                      </span>
                    </div>
                    <Progress value={job.progress_percent} className="h-2" />
                    <p className="text-xs text-muted-foreground text-right">
                      {job.progress_percent}%
                    </p>
                  </div>
                ))
              )}

              {trainingJobs.length > 0 &&
                trainingJobs.every(job => job.status === 'completed' || job.status === 'failed') && (
                  <div className="pt-4 border-t">
                    <div className="flex justify-between items-center">
                      <p className="text-sm text-muted-foreground">
                        {trainingJobs.filter(j => j.status === 'completed').length} of{' '}
                        {trainingJobs.length} models trained successfully
                      </p>
                      <Button onClick={() => router.push('/models/comparison')}>
                        View Results
                      </Button>
                    </div>
                  </div>
                )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
