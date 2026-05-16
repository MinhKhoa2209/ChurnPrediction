/**
 * Datasets API Client
 * Handles dataset-related API requests
 */

import { api } from './api';

export interface Dataset {
  id: string;
  user_id: string;
  filename: string;
  record_count: number;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  validation_errors: any;
  data_quality_score: number | null;
  uploaded_at: string;
  processed_at: string | null;
}

/**
 * Get dataset details by ID
 */
export async function getDataset(
  datasetId: string,
  token: string
): Promise<Dataset> {
  return api.get<Dataset>(`/datasets/${datasetId}`, token);
}

/**
 * List all datasets for the current user
 */
export async function listDatasets(token: string): Promise<{ datasets: Dataset[]; total: number }> {
  return api.get<{ datasets: Dataset[]; total: number }>('/datasets', token);
}
