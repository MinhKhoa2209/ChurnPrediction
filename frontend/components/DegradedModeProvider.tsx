"use client";

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
    markConnected,
  } = useDegradedModeStore();

  useEffect(() => {
    queueMicrotask(() => {
      setBannerDismissed(false);
    });
  }, [degradedMode, backendUnreachable]);

  useEffect(() => {
    if (!backendUnreachable) {
      return;
    }

    console.log("Backend unreachable, starting auto-reconnect...");

    const checkHealth = async (): Promise<boolean> => {
      try {
        const response = await fetch("/api/v1/health", {
          method: "GET",
          cache: "no-store",
        });
        return response.ok;
      } catch {
        return false;
      }
    };

    const cleanup = startAutoReconnect(checkHealth, () => {
      console.log("Backend recovered, refreshing data...");
      window.location.reload();
    });

    return cleanup;
  }, [backendUnreachable]);

  const handleRetry = async () => {
    try {
      const response = await fetch("/api/v1/health", {
        method: "GET",
        cache: "no-store",
      });

      if (response.ok) {
        markConnected();
        window.location.reload();
      }
    } catch (error) {
      console.error("Manual retry failed:", error);
    }
  };

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
