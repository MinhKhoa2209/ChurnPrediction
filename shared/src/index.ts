/**
 * Shared TypeScript Types
 * Customer Churn Prediction Platform
 */

// User and Authentication Types
export interface User {
  id: string;
  email: string;
  role: 'Admin' | 'Data_Scientist' | 'Analyst';
  createdAt: string;
  emailVerified: boolean;
  emailNotificationsEnabled: boolean;
}

export interface AuthTokens {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role?: 'Data_Scientist' | 'Analyst';
}

// Dataset Types
export interface Dataset {
  id: string;
  userId: string;
  filename: string;
  recordCount: number;
  uploadedAt: string;
  processedAt?: string;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  validationErrors?: Record<string, string[]>;
  dataQualityScore?: number;
}

export interface CustomerRecord {
  id: string;
  datasetId: string;
  gender?: string;
  seniorCitizen?: number;
  partner?: string;
  dependents?: string;
  tenure?: number;
  phoneService?: string;
  multipleLines?: string;
  internetService?: string;
  onlineSecurity?: string;
  onlineBackup?: string;
  deviceProtection?: string;
  techSupport?: string;
  streamingTv?: string;
  streamingMovies?: string;
  contract?: string;
  paperlessBilling?: string;
  monthlyCharges?: number;
  totalCharges?: number;
  churn?: boolean;
}

// Model Types
export type ModelType = 'KNN' | 'NaiveBayes' | 'DecisionTree' | 'SVM';

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  rocAuc: number;
}

export interface ModelVersion {
  id: string;
  userId: string;
  datasetId: string;
  modelType: ModelType;
  version: string;
  hyperparameters: Record<string, any>;
  metrics: ModelMetrics;
  confusionMatrix: number[][];
  trainingTime: number;
  trainedAt: string;
  status: 'active' | 'archived';
  classificationThreshold: number;
  mlflowRunId?: string;
}

// Training Job Types
export type TrainingJobStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface TrainingJob {
  id: string;
  userId: string;
  datasetId: string;
  modelVersionId?: string;
  modelType: ModelType;
  status: TrainingJobStatus;
  progress: number;
  currentIteration?: number;
  totalIterations?: number;
  estimatedTimeRemaining?: number;
  error?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface TrainingProgress {
  iteration: number;
  metricValue: number;
  metricName: string;
  recordedAt: string;
}

// Prediction Types
export interface PredictionInput {
  gender: string;
  seniorCitizen: number;
  partner: string;
  dependents: string;
  tenure: number;
  phoneService: string;
  multipleLines: string;
  internetService: string;
  onlineSecurity: string;
  onlineBackup: string;
  deviceProtection: string;
  techSupport: string;
  streamingTv: string;
  streamingMovies: string;
  contract: string;
  paperlessBilling: string;
  paymentMethod: string;
  monthlyCharges: number;
  totalCharges: number;
}

export interface SHAPValue {
  feature: string;
  value: number | string;
  contribution: number;
}

export interface Prediction {
  id: string;
  userId: string;
  modelVersionId: string;
  inputFeatures: PredictionInput;
  probability: number;
  threshold: number;
  prediction: boolean;
  shapValues: SHAPValue[];
  isBatch: boolean;
  batchId?: string;
  createdAt: string;
}

// Dashboard Types
export interface DashboardMetrics {
  totalCustomers: number;
  churnRate: number;
  atRiskCount: number;
  churnDistribution: {
    churned: number;
    retained: number;
  };
  monthlyTrend: Array<{
    month: string;
    churnRate: number;
  }>;
}

// EDA Types
export interface CorrelationMatrix {
  features: string[];
  matrix: number[][];
}

export interface DistributionData {
  feature: string;
  bins: number[];
  counts: number[];
}

export interface ChurnByCategory {
  category: string;
  values: Array<{
    value: string;
    churnRate: number;
    count: number;
  }>;
}

// Feature Engineering Types
export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface PCAResult {
  components: number[][];
  explainedVariance: number[];
  labels: boolean[];
}

// Report Types
export interface Report {
  id: string;
  userId: string;
  modelVersionId?: string;
  reportType: string;
  filePath: string;
  metadata?: Record<string, any>;
  generatedAt: string;
}

// Notification Types
export interface Notification {
  id: string;
  userId: string;
  trainingJobId?: string;
  notificationType: string;
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
  readAt?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  error: string;
  message: string;
  requestId?: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'training_progress' | 'training_complete' | 'training_failed' | 'notification';
  payload: any;
  timestamp: string;
}
