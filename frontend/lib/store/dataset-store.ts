import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface Dataset {
  id: string;
  filename: string;
  status: 'processing' | 'ready' | 'failed';
  message: string;
  uploaded_at: string;
  record_count?: number;
  validation_errors?: Record<string, unknown>;
}

interface DatasetState {
  datasets: Dataset[];
  currentDataset: Dataset | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  
  // Actions
  setDatasets: (datasets: Dataset[]) => void;
  addDataset: (dataset: Dataset) => void;
  updateDataset: (id: string, updates: Partial<Dataset>) => void;
  setCurrentDataset: (dataset: Dataset | null) => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setUploadError: (error: string | null) => void;
  resetUpload: () => void;
}

export const useDatasetStore = create<DatasetState>()(
  persist(
    (set) => ({
      datasets: [],
      currentDataset: null,
      isUploading: false,
      uploadProgress: 0,
      uploadError: null,
      
      setDatasets: (datasets) => set({ datasets }),
      
      addDataset: (dataset) => set((state) => ({
        datasets: [
          dataset,
          ...state.datasets.filter((existingDataset) => existingDataset.id !== dataset.id),
        ],
      })),
      
      updateDataset: (id, updates) => set((state) => ({
        datasets: state.datasets.map((d) =>
          d.id === id ? { ...d, ...updates } : d
        ),
        currentDataset:
          state.currentDataset?.id === id
            ? { ...state.currentDataset, ...updates }
            : state.currentDataset,
      })),
      
      setCurrentDataset: (dataset) => set({ currentDataset: dataset }),
      
      setUploading: (uploading) => set({ isUploading: uploading }),
      
      setUploadProgress: (progress) => set({ uploadProgress: progress }),
      
      setUploadError: (error) => set({ uploadError: error }),
      
      resetUpload: () => set({
        isUploading: false,
        uploadProgress: 0,
        uploadError: null,
      }),
    }),
    {
      name: 'dataset-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        datasets: state.datasets,
        currentDataset: state.currentDataset,
      }),
    }
  )
);
