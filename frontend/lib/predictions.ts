import { api, API_BASE_URL } from './api';

export interface PredictionInput {
  gender: 'Male' | 'Female';
  SeniorCitizen: 0 | 1;
  Partner: 'Yes' | 'No';
  Dependents: 'Yes' | 'No';
  tenure: number;
  PhoneService: 'Yes' | 'No';
  MultipleLines: 'Yes' | 'No' | 'No phone service';
  InternetService: 'DSL' | 'Fiber optic' | 'No';
  OnlineSecurity: 'Yes' | 'No' | 'No internet service';
  OnlineBackup: 'Yes' | 'No' | 'No internet service';
  DeviceProtection: 'Yes' | 'No' | 'No internet service';
  TechSupport: 'Yes' | 'No' | 'No internet service';
  StreamingTV: 'Yes' | 'No' | 'No internet service';
  StreamingMovies: 'Yes' | 'No' | 'No internet service';
  Contract: 'Month-to-month' | 'One year' | 'Two year';
  PaperlessBilling: 'Yes' | 'No';
  PaymentMethod: 'Electronic check' | 'Mailed check' | 'Bank transfer (automatic)' | 'Credit card (automatic)';
  MonthlyCharges: number;
  TotalCharges: number;
}

export interface ShapContribution {
  feature: string;
  value: number | string;
  contribution: number;
  direction: 'positive' | 'negative';
}

export interface ShapValues {
  base_value: number;
  prediction_value: number;
  top_positive: ShapContribution[];
  top_negative: ShapContribution[];
}

export interface PredictionResponse {
  id: string;
  model_version_id: string;
  probability: number;
  threshold: number;
  prediction: 'Churn' | 'No Churn';
  shap_values: ShapValues;
  created_at: string;
}

export interface SinglePredictionRequest {
  model_version_id: string;
  input: PredictionInput;
}

export async function createSinglePrediction(
  request: SinglePredictionRequest,
  token: string
): Promise<PredictionResponse> {
  return api.post<PredictionResponse>('/predictions/single', request, token);
}

export interface BatchPredictionUploadResponse {
  batch_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  record_count: number;
  message: string;
}

export interface BatchPredictionResult {
  id: string;
  batch_id: string;
  input_features: PredictionInput;
  probability: number;
  threshold: number;
  prediction: 'Churn' | 'No Churn';
  created_at: string;
}

export interface BatchPredictionResultsResponse {
  batch_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  record_count: number;
  processed_count: number;
  results: BatchPredictionResult[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function uploadBatchPrediction(
  file: File,
  modelVersionId: string,
  token: string,
  onProgress?: (progress: number) => void
): Promise<BatchPredictionUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('model_version_id', modelVersionId);

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          onProgress(progress);
        }
      });
    }

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error('Failed to parse response'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || error.message || 'Batch upload failed'));
        } catch {
          reject(new Error(xhr.statusText || 'Batch upload failed'));
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error during batch upload'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Batch upload aborted'));
    });

    xhr.open('POST', `${API_BASE_URL}/predictions/batch`);
    
    // Set headers
    Object.entries(headers).forEach(([key, value]) => {
      xhr.setRequestHeader(key, value);
    });

    xhr.send(formData);
  });
}

export async function getBatchPredictionResults(
  batchId: string,
  token: string,
  page: number = 1,
  pageSize: number = 50
): Promise<BatchPredictionResultsResponse> {
  return api.get<BatchPredictionResultsResponse>(
    `/predictions/batch/${batchId}?page=${page}&page_size=${pageSize}`,
    token
  );
}

export async function downloadBatchPredictionCSV(
  batchId: string,
  token: string
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/predictions/batch/${batchId}/export`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: 'Unknown error',
      message: response.statusText,
    }));
    throw new Error(error.message || 'Failed to download CSV');
  }

  return response.blob();
}

export function getProbabilityColor(probability: number): {
  bg: string;
  text: string;
  border: string;
  label: string;
} {
  const percentage = probability * 100;
  
  if (percentage < 30) {
    return {
      bg: 'bg-green-50 dark:bg-green-900/20',
      text: 'text-green-700 dark:text-green-300',
      border: 'border-green-500',
      label: 'Low Risk'
    };
  } else if (percentage < 70) {
    return {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      text: 'text-yellow-700 dark:text-yellow-300',
      border: 'border-yellow-500',
      label: 'Medium Risk'
    };
  } else {
    return {
      bg: 'bg-red-50 dark:bg-red-900/20',
      text: 'text-red-700 dark:text-red-300',
      border: 'border-red-500',
      label: 'High Risk'
    };
  }
}
