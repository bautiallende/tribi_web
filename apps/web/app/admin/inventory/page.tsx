"use client";

import { apiUrl } from "@/lib/apiConfig";
import {
  Badge,
  Input,
  Pagination,
  SearchInput,
  Select,
  Skeleton,
  useToast,
} from "@tribi/ui";
import { useCallback, useEffect, useMemo, useState } from "react";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface AdminInventoryItem {
  id: number;
  plan_id?: number | null;
  carrier_id?: number | null;
  country_id?: number | null;
  status: string;
  activation_code?: string | null;
  iccid?: string | null;
  provider_reference?: string | null;
  reserved_at?: string | null;
  assigned_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

interface AdminStockAlert {
  plan_id: number;
  plan_name: string;
  available: number;
}

interface AdminInventoryStats {
  totals: Record<string, number>;
  low_stock_threshold: number;
  low_stock_alerts: AdminStockAlert[];
}

const pageSize = 20;

const statusOptions = [
  { label: "All statuses", value: "all" },
  { label: "Available", value: "available" },
  { label: "Reserved", value: "reserved" },
  { label: "Assigned", value: "assigned" },
  { label: "Retired", value: "retired" },
];

const statusVariant = (status: string) => {
  const normalized = status?.toLowerCase();
  if (normalized === "available") return "success" as const;
  if (normalized === "reserved") return "warning" as const;
  if (normalized === "assigned") return "primary" as const;
  if (normalized === "retired") return "outline" as const;
  return "default" as const;
};

const getAuthHeaders = (): HeadersInit => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function AdminInventoryPage() {
  const { showToast } = useToast();
  const [items, setItems] = useState<AdminInventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [planId, setPlanId] = useState("");
  const [carrierId, setCarrierId] = useState("");
  const [countryId, setCountryId] = useState("");

  const [stats, setStats] = useState<AdminInventoryStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [lowStockThreshold, setLowStockThreshold] = useState(10);

  const statusTotals = useMemo(() => {
    const totals = stats?.totals || {};
    return {
      available: totals.available || 0,
      reserved: totals.reserved || 0,
      assigned: totals.assigned || 0,
      retired: totals.retired || 0,
    };
  }, [stats]);

  const fetchInventory = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) params.set("q", search);
      if (status !== "all") params.set("inventory_status", status);
      if (planId.trim()) params.set("plan_id", planId.trim());
      if (carrierId.trim()) params.set("carrier_id", carrierId.trim());
      if (countryId.trim()) params.set("country_id", countryId.trim());

      const response = await fetch(
        apiUrl(`/admin/inventory?${params.toString()}`),
        {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
        },
      );

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Unable to load inventory");
      }

      const data: PaginatedResponse<AdminInventoryItem> = await response.json();
      setItems(data.items);
      setTotalItems(data.total);
      setTotalPages(data.total_pages);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load inventory", "error");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, status, planId, carrierId, countryId, showToast]);

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const params = new URLSearchParams({
        low_stock_threshold: lowStockThreshold.toString(),
      });
      const response = await fetch(
        apiUrl(`/admin/inventory/stats?${params.toString()}`),
        {
          credentials: "include",
          headers: {
            ...getAuthHeaders(),
          },
        },
      );
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Unable to load inventory stats");
      }
      const data: AdminInventoryStats = await response.json();
      setStats(data);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load inventory stats", "error");
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, [lowStockThreshold, showToast]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const handleStatusChange = (value: string) => {
    setStatus(value);
    setPage(1);
  };

  const handlePlanChange = (value: string) => {
    setPlanId(value);
    setPage(1);
  };

  const handleCarrierChange = (value: string) => {
    setCarrierId(value);
    setPage(1);
  };

  const handleCountryChange = (value: string) => {
    setCountryId(value);
    setPage(1);
  };

  const handleThresholdChange = (value: string) => {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      setLowStockThreshold(Math.min(1000, Math.max(1, parsed)));
    } else {
      setLowStockThreshold(1);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Inventory
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Track eSIM stock by status, inspect assignments, and configure
          low-stock alerts.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {(["available", "reserved", "assigned", "retired"] as const).map(
          (statusKey) => (
            <div
              key={statusKey}
              className="rounded-xl border-2 border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-slate-800"
            >
              <p className="text-sm text-gray-500 capitalize">{statusKey}</p>
              <div className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                {statsLoading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  statusTotals[statusKey]
                )}
              </div>
            </div>
          ),
        )}
      </div>

      <div className="rounded-xl border-2 border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-800">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Low Stock Alerts
            </h2>
            <p className="text-sm text-gray-600">
              Plans below the configured available count threshold.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Threshold
            </label>
            <Input
              type="number"
              min={1}
              max={1000}
              value={lowStockThreshold}
              onChange={(e) => handleThresholdChange(e.target.value)}
              className="w-24"
            />
          </div>
        </div>
        <div className="mt-4 divide-y divide-gray-200 text-sm dark:divide-gray-700">
          {statsLoading ? (
            Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="py-3">
                <Skeleton className="h-4 w-48" />
              </div>
            ))
          ) : stats && stats.low_stock_alerts.length > 0 ? (
            stats.low_stock_alerts.map((alert) => (
              <div
                key={alert.plan_id}
                className="flex items-center justify-between py-3"
              >
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {alert.plan_name || `Plan #${alert.plan_id}`}
                  </p>
                  <p className="text-xs text-gray-500">Plan #{alert.plan_id}</p>
                </div>
                <Badge variant="warning">{alert.available} available</Badge>
              </div>
            ))
          ) : (
            <p className="py-3 text-gray-500">
              No plans are below the low-stock threshold.
            </p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="md:col-span-2">
          <SearchInput
            placeholder="Search activation code or ICCID..."
            onSearch={handleSearch}
            debounceMs={300}
          />
        </div>
        <Select
          value={status}
          onChange={(e) => handleStatusChange(e.target.value)}
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Input
          type="number"
          min={1}
          value={planId}
          onChange={(e) => handlePlanChange(e.target.value)}
          placeholder="Plan ID"
        />
        <Input
          type="number"
          min={1}
          value={carrierId}
          onChange={(e) => handleCarrierChange(e.target.value)}
          placeholder="Carrier ID"
        />
        <Input
          type="number"
          min={1}
          value={countryId}
          onChange={(e) => handleCountryChange(e.target.value)}
          placeholder="Country ID"
        />
      </div>

      <div className="overflow-hidden rounded-xl border-2 border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-slate-700 dark:text-gray-300">
              <tr>
                <th className="px-6 py-4">Inventory</th>
                <th className="px-6 py-4">Associations</th>
                <th className="px-6 py-4">Metadata</th>
                <th className="px-6 py-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={idx}>
                    {Array.from({ length: 4 }).map((__, cell) => (
                      <td key={cell} className="px-6 py-4">
                        <Skeleton className="h-4 w-24" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    No inventory items match the current filters.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-gray-50 dark:hover:bg-slate-700/40"
                  >
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          #{item.id}
                        </div>
                        <Badge variant={statusVariant(item.status)}>
                          {item.status}
                        </Badge>
                        {item.activation_code && (
                          <div className="text-xs font-mono text-gray-600">
                            {item.activation_code}
                          </div>
                        )}
                        {item.iccid && (
                          <div className="text-xs font-mono text-gray-600">
                            {item.iccid}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-900 dark:text-white">
                      <div>Plan #{item.plan_id ?? "—"}</div>
                      <div className="text-xs text-gray-600">
                        Carrier #{item.carrier_id ?? "—"}
                      </div>
                      <div className="text-xs text-gray-600">
                        Country #{item.country_id ?? "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {item.provider_reference || "—"}
                      </div>
                      <div className="text-xs text-gray-500">
                        Reserved:{" "}
                        {item.reserved_at
                          ? dateFormatter.format(new Date(item.reserved_at))
                          : "—"}
                      </div>
                      <div className="text-xs text-gray-500">
                        Assigned:{" "}
                        {item.assigned_at
                          ? dateFormatter.format(new Date(item.assigned_at))
                          : "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {dateFormatter.format(new Date(item.created_at))}
                      {item.updated_at && (
                        <div className="text-xs text-gray-500">
                          Updated{" "}
                          {dateFormatter.format(new Date(item.updated_at))}
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Pagination
        currentPage={page}
        totalPages={totalPages}
        onPageChange={setPage}
        totalItems={totalItems}
        itemsPerPage={pageSize}
      />
    </div>
  );
}
