import { create } from "zustand";

interface DegradedModeState {
  degradedMode: boolean;
  backendUnreachable: boolean;
  cachedData: Record<string, any>;
  lastConnected: Date | null;
  reconnecting: boolean;
  reconnectAttempts: number;
  setDegradedMode: (degraded: boolean) => void;
  setBackendUnreachable: (unreachable: boolean) => void;
  cacheData: (key: string, data: any) => void;
  getCachedData: (key: string) => any;
  clearCachedData: (key?: string) => void;
  markConnected: () => void;
  startReconnect: () => void;
  completeReconnect: (success: boolean) => void;
  reset: () => void;
}

export const useDegradedModeStore = create<DegradedModeState>((set, get) => ({
  degradedMode: false,
  backendUnreachable: false,
  cachedData: {},
  lastConnected: null,
  reconnecting: false,
  reconnectAttempts: 0,

  setDegradedMode: (degraded) => {
    set({ degradedMode: degraded });
    if (!degraded) {
      // If no longer degraded, mark as connected
      set({ lastConnected: new Date(), reconnectAttempts: 0 });
    }
  },

  setBackendUnreachable: (unreachable) => {
    set({ backendUnreachable: unreachable });
    if (!unreachable) {
      // If backend is reachable again, mark as connected
      set({ lastConnected: new Date(), reconnectAttempts: 0 });
    }
  },

  cacheData: (key, data) => {
    set((state) => ({
      cachedData: {
        ...state.cachedData,
        [key]: {
          data,
          timestamp: new Date().toISOString(),
        },
      },
    }));
  },

  getCachedData: (key) => {
    const cached = get().cachedData[key];
    return cached?.data;
  },

  clearCachedData: (key) => {
    if (key) {
      set((state) => {
        const newCachedData = { ...state.cachedData };
        delete newCachedData[key];
        return { cachedData: newCachedData };
      });
    } else {
      set({ cachedData: {} });
    }
  },

  markConnected: () => {
    set({
      lastConnected: new Date(),
      degradedMode: false,
      backendUnreachable: false,
      reconnecting: false,
      reconnectAttempts: 0,
    });
  },

  startReconnect: () => {
    set((state) => ({
      reconnecting: true,
      reconnectAttempts: state.reconnectAttempts + 1,
    }));
  },

  completeReconnect: (success) => {
    if (success) {
      set({
        reconnecting: false,
        backendUnreachable: false,
        degradedMode: false,
        lastConnected: new Date(),
        reconnectAttempts: 0,
      });
    } else {
      set({ reconnecting: false });
    }
  },

  reset: () => {
    set({
      degradedMode: false,
      backendUnreachable: false,
      cachedData: {},
      lastConnected: null,
      reconnecting: false,
      reconnectAttempts: 0,
    });
  },
}));

export const RECONNECT_CONFIG = {
  MAX_ATTEMPTS: 5,
  INITIAL_DELAY: 2000,
  MAX_DELAY: 30000,
  BACKOFF_MULTIPLIER: 2,
};

export function getReconnectDelay(attemptNumber: number): number {
  const delay = Math.min(
    RECONNECT_CONFIG.INITIAL_DELAY * Math.pow(RECONNECT_CONFIG.BACKOFF_MULTIPLIER, attemptNumber - 1),
    RECONNECT_CONFIG.MAX_DELAY
  );
  return delay;
}
