import { create } from 'zustand';

// ── EDA Data Types ──────────────────────────────────────────────

export interface FeatureDistribution {
  bins: number[];
  frequencies: number[];
  min: number;
  max: number;
  mean: number;
  median: number;
}

export interface CorrelationData {
  datasetId: string;
  features: string[];
  correlationMatrix: number[][];
  recordCount: number;
}

export interface DistributionsData {
  datasetId: string;
  distributions: {
    tenure: FeatureDistribution;
    MonthlyCharges: FeatureDistribution;
    TotalCharges: FeatureDistribution;
  };
  recordCount: number;
}

export interface ChurnRateItem {
  contractType?: string;
  internetServiceType?: string;
  churnRate: number;
  totalCustomers: number;
  churnedCustomers: number;
}

export interface ChurnByContractData {
  datasetId: string;
  churnRates: ChurnRateItem[];
  recordCount: number;
}

export interface ChurnByInternetData {
  datasetId: string;
  churnRates: ChurnRateItem[];
  recordCount: number;
}

export interface ScatterDataPoint {
  monthlyCharges: number;
  totalCharges: number;
  churn: boolean;
}

export interface ScatterPlotData {
  datasetId: string;
  scatterData: ScatterDataPoint[];
  recordCount: number;
}

// ── Cached EDA Entry ────────────────────────────────────────────

export interface CachedEDAData {
  correlationData: CorrelationData | null;
  distributionsData: DistributionsData | null;
  churnByContractData: ChurnByContractData | null;
  churnByInternetData: ChurnByInternetData | null;
  scatterData: ScatterPlotData | null;
  fetchedAt: number; // timestamp
}

// ── Store State ─────────────────────────────────────────────────

interface EDAState {
  // Cache keyed by datasetId
  cache: Record<string, CachedEDAData>;

  // Loading state per dataset
  loadingDatasets: Record<string, boolean>;

  // Active tab (persisted across navigations)
  activeTab: string;

  // Actions
  setCachedData: (datasetId: string, data: Omit<CachedEDAData, 'fetchedAt'>) => void;
  getCachedData: (datasetId: string) => CachedEDAData | null;
  isCacheValid: (datasetId: string, maxAgeMs?: number) => boolean;
  setLoading: (datasetId: string, loading: boolean) => void;
  isLoading: (datasetId: string) => boolean;
  setActiveTab: (tab: string) => void;
  invalidateCache: (datasetId: string) => void;
  clearAllCache: () => void;
}

// Cache is valid for 10 minutes by default
const DEFAULT_CACHE_MAX_AGE_MS = 10 * 60 * 1000;

export const useEDAStore = create<EDAState>()((set, get) => ({
  cache: {},
  loadingDatasets: {},
  activeTab: 'overview',

  setCachedData: (datasetId, data) =>
    set((state) => ({
      cache: {
        ...state.cache,
        [datasetId]: {
          ...data,
          fetchedAt: Date.now(),
        },
      },
    })),

  getCachedData: (datasetId) => {
    return get().cache[datasetId] || null;
  },

  isCacheValid: (datasetId, maxAgeMs = DEFAULT_CACHE_MAX_AGE_MS) => {
    const cached = get().cache[datasetId];
    if (!cached) return false;
    return Date.now() - cached.fetchedAt < maxAgeMs;
  },

  setLoading: (datasetId, loading) =>
    set((state) => ({
      loadingDatasets: {
        ...state.loadingDatasets,
        [datasetId]: loading,
      },
    })),

  isLoading: (datasetId) => {
    return get().loadingDatasets[datasetId] || false;
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  invalidateCache: (datasetId) =>
    set((state) => {
      const newCache = { ...state.cache };
      delete newCache[datasetId];
      return { cache: newCache };
    }),

  clearAllCache: () => set({ cache: {}, loadingDatasets: {} }),
}));
