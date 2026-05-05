"use client";

/**
 * Degraded Mode Provider
 * 
 * Provides global degraded mode detection and auto-reconnect functionality

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { DegradedModeBanner } from "./DegradedModeBanner";
import { useDegradedModeStore } from "@/lib/store/degradedModeStore";
import { startAutoReconnect } from "@/lib/apiInterceptor";

interface DegradedModeProviderProps {
  children: React.ReactNode;
}

export function DegradedModeProvider({ children }: DegradedModeProviderProps) {
  const pathname = usePathname();
  const [bannerDismissed, setBannerDismissed] = useState(false);
  
  const {
    degradedMode,
    backendUnreachable,
    reconnecting,
    markConnected,
  } = useDegradedModeStore();

  // Reset banner dismissed state when mode changes
  useEffect(() => {
    setBannerDismissed(false);
  }, [degradedMode, backendUnreachable]);

  // Start auto-reconnect when backend becomes unreachable
  useEffect(() => {
    if (!backendUnreachable) {
      return;
    }

    console.log("Backend unreachable, starting auto-reconnect...");

    // Health check function
    const checkHealth = async (): Promise<boolean> => {
      try {
        const response = await fetch("/api/v1/health", {
          method: "GET",
          cache: "no-store",
        });
        return response.ok;
      } catch (error) {
        return false;
      }
    };

    // Start auto-reconnect with callback to refresh page data
    const cleanup = startAutoReconnect(checkHealth, () => {
      console.log("Backend recovered, refreshing data...");
      // Trigger a page refresh to reload data
      window.location.reload();
    });

    return cleanup;
  }, [backendUnreachable]);

  // Manual retry handler
  const handleRetry = async () => {
    try {
      const response = await fetch("/api/v1/health", {
        method: "GET",
        cache: "no-store",
      });

      if (response.ok) {
        markConnected();
        // Refresh the page to reload data
        window.location.reload();
      }
    } catch (error) {
      console.error("Manual retry failed:", error);
    }
  };

  // Don't show banner on login/register pages
  const isAuthPage = pathname === "/login" || pathname === "/register";

  return (
    <>
      {!isAuthPage && !bannerDismissed && (
        <DegradedModeBanner
          degradedMode={degradedMode}
          backendUnreachable={backendUnreachable}
          onDismiss={() => setBannerDismissed(true)}
          onRetry={handleRetry}
        />
      )}
      {children}
    </>
  );
}
