import { api } from './api';
export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
}
export interface ModelVersion {
  id: string;
  user_id: string;
  dataset_id: string;
  preprocessing_config_id: string;
  model_type: 'KNN' | 'NaiveBayes' | 'DecisionTree' | 'SVM';
  version: string;
  hyperparameters: Record<string, any>;
  metrics: ModelMetrics;
  confusion_matrix: number[][];
  training_time_seconds: number;
  artifact_path: string;
  mlflow_run_id: string | null;
  status: 'active' | 'archived';
  classification_threshold: number;
  trained_at: string;
  archived_at: string | null;
}
export interface ModelVersionListItem extends ModelVersion {}
export interface ModelVersionListResponse {
  versions: ModelVersionListItem[];
  total: number;
}
export interface ConfusionMatrixData {
  matrix: number[][];
  labels: string[];
}
export interface ROCCurvePoint {
  fpr: number;
  tpr: number;
  threshold: number;
}
export interface ROCCurveData {
  points: ROCCurvePoint[];
  auc: number;
}
export interface TrainingJob {
  id: string;
  user_id: string;
  dataset_id: string;
  model_version_id: string | null;
  model_type: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress_percent: number;
  current_iteration: number | null;
  total_iterations: number | null;
  estimated_seconds_remaining: number | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}
export interface TrainingJobListResponse {
  jobs: TrainingJob[];
  total: number;
}
export interface TrainingJobCreateRequest {
  dataset_id: string;
  model_types: string[];
  hyperparameters?: Record<string, any>;
}
export interface TrainingJobCreateResponse {
  jobs: TrainingJob[];
  message: string;
}
export async function listModelVersions(
  token: string,
  filters?: {
    model_type?: string;
    status?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }
): Promise<ModelVersionListResponse> {
  const params = new URLSearchParams();
  if (filters?.model_type) params.append('model_type', filters.model_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.sort_by) params.append('sort_by', filters.sort_by);
  if (filters?.sort_order) params.append('sort_order', filters.sort_order);
  const queryString = params.toString();
  const endpoint = `/models/versions${queryString ? `?${queryString}` : ''}`;
  return api.get<ModelVersionListResponse>(endpoint, token);
}
export async function getModelVersion(
  versionId: string,
  token: string
): Promise<ModelVersion> {
  return api.get<ModelVersion>(`/models/versions/${versionId}`, token);
}
export async function getModelMetrics(
  versionId: string,
  token: string
): Promise<ModelMetrics> {
  return api.get<ModelMetrics>(`/models/versions/${versionId}/metrics`, token);
}
export async function getConfusionMatrix(
  versionId: string,
  token: string
): Promise<ConfusionMatrixData> {
  return api.get<ConfusionMatrixData>(
    `/models/versions/${versionId}/confusion-matrix`,
    token
  );
}
export async function getROCCurve(
  versionId: string,
  token: string
): Promise<ROCCurveData> {
  return api.get<ROCCurveData>(`/models/versions/${versionId}/roc-curve`, token);
}
export async function updateThreshold(
  versionId: string,
  threshold: number,
  token: string
): Promise<{ id: string; classification_threshold: number; message: string }> {
  return api.patch(
    `/models/versions/${versionId}/threshold`,
    { threshold },
    token
  );
}
export async function archiveModelVersion(
  versionId: string,
  archive: boolean,
  token: string
): Promise<{ id: string; status: string; message: string }> {
  return api.post(`/models/versions/${versionId}/archive`, { archive }, token);
}
export async function createTrainingJob(
  request: TrainingJobCreateRequest,
  token: string
): Promise<TrainingJobCreateResponse> {
  return api.post<TrainingJobCreateResponse>('/models/train', request, token);
}
export async function listTrainingJobs(
  token: string,
  statusFilter?: string
): Promise<TrainingJobListResponse> {
  const params = statusFilter ? `?status_filter=${statusFilter}` : '';
  return api.get<TrainingJobListResponse>(`/models/jobs${params}`, token);
}
export async function getTrainingJob(
  jobId: string,
  token: string
): Promise<TrainingJob> {
  return api.get<TrainingJob>(`/models/jobs/${jobId}`, token);
}
export async function deleteTrainingJob(
  jobId: string,
  token: string
): Promise<void> {
  return api.delete(`/models/jobs/${jobId}`, token);
}