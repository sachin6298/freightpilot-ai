import { useState, useEffect, useCallback } from "react";
import { fetchAnalyticsOverview, fetchShipments, fetchShipmentPayments, fetchNotifications } from "../api";

interface DashboardData {
  analytics: any;
  shipments: any[];
  payments: any[];
  notifications: any[];
  loading: boolean;
  error: string | null;
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData>({
    analytics: null,
    shipments: [],
    payments: [],
    notifications: [],
    loading: true,
    error: null,
  });

  const loadData = useCallback(async () => {
    try {
      setData((prev) => ({ ...prev, loading: true, error: null }));

      const [analyticsResult, shipmentsResult, notificationsResult] = await Promise.allSettled([
        fetchAnalyticsOverview(),
        fetchShipments(),
        fetchNotifications(),
      ]);

      let paymentData: any[] = [];
      if (shipmentsResult.status === "fulfilled" && shipmentsResult.value.length > 0) {
        const paymentResults = await Promise.allSettled(
          shipmentsResult.value.slice(0, 5).map((s: any) => fetchShipmentPayments(s.id))
        );
        paymentData = paymentResults
          .filter((r): r is PromiseFulfilledResult<any[]> => r.status === "fulfilled")
          .flatMap((r) => r.value);
      }

      setData({
        analytics: analyticsResult.status === "fulfilled" ? analyticsResult.value : null,
        shipments: shipmentsResult.status === "fulfilled" ? shipmentsResult.value : [],
        payments: paymentData,
        notifications: notificationsResult.status === "fulfilled" ? notificationsResult.value : [],
        loading: false,
        error: null,
      });
    } catch (err) {
      setData((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load dashboard data",
      }));
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return { ...data, refresh: loadData };
}
