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
import { useCallback, useEffect, useState } from "react";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface AdminUserSummary {
  id: number;
  email: string;
  name?: string | null;
}

interface AdminEsimProfile {
  id: number;
  status: string;
  activation_code?: string | null;
  iccid?: string | null;
  order_id?: number | null;
  plan_id?: number | null;
  inventory_item_id?: number | null;
  created_at: string;
  user?: AdminUserSummary | null;
}

const pageSize = 20;

const esimStatusOptions = [
  { label: "All statuses", value: "all" },
  { label: "Draft", value: "draft" },
  { label: "Pending Activation", value: "pending_activation" },
  { label: "Reserved", value: "reserved" },
  { label: "Assigned", value: "assigned" },
  { label: "Active", value: "active" },
  { label: "Failed", value: "failed" },
  { label: "Expired", value: "expired" },
];

const inventoryStatusOptions = [
  { label: "Any inventory state", value: "all" },
  { label: "Available", value: "available" },
  { label: "Reserved", value: "reserved" },
  { label: "Assigned", value: "assigned" },
  { label: "Retired", value: "retired" },
];

const getAuthHeaders = (): HeadersInit => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const esimStatusVariant = (status: string) => {
  const normalized = status?.toLowerCase();
  if (normalized === "active") return "success" as const;
  if (normalized === "assigned") return "primary" as const;
  if (normalized === "reserved") return "warning" as const;
  if (normalized === "failed") return "destructive" as const;
  if (normalized === "pending_activation") return "accent" as const;
  return "default" as const;
};

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function AdminEsimsPage() {
  const { showToast } = useToast();
  const [profiles, setProfiles] = useState<AdminEsimProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [search, setSearch] = useState("");
  const [esimStatus, setEsimStatus] = useState("all");
  const [inventoryStatus, setInventoryStatus] = useState("all");
  const [orderId, setOrderId] = useState("");

  const fetchProfiles = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) params.set("user_q", search);
      if (esimStatus !== "all") params.set("esim_status", esimStatus);
      if (inventoryStatus !== "all")
        params.set("inventory_status", inventoryStatus);
      if (orderId.trim()) params.set("order_id", orderId.trim());

      const response = await fetch(
        apiUrl(`/admin/esims?${params.toString()}`),
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
        throw new Error(err.detail || "Unable to load eSIM profiles");
      }

      const data: PaginatedResponse<AdminEsimProfile> = await response.json();
      setProfiles(data.items);
      setTotalItems(data.total);
      setTotalPages(data.total_pages);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load eSIMs", "error");
      setProfiles([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, esimStatus, inventoryStatus, orderId, showToast]);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const handleStatusChange = (value: string) => {
    setEsimStatus(value);
    setPage(1);
  };

  const handleInventoryStatusChange = (value: string) => {
    setInventoryStatus(value);
    setPage(1);
  };

  const handleOrderIdChange = (value: string) => {
    setOrderId(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          eSIM Profiles
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitor provisioning status and inventory assignments per customer.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="md:col-span-2">
          <SearchInput
            placeholder="Search by user email or name..."
            onSearch={handleSearch}
            debounceMs={300}
          />
        </div>
        <Select
          value={esimStatus}
          onChange={(e) => handleStatusChange(e.target.value)}
        >
          {esimStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={inventoryStatus}
          onChange={(e) => handleInventoryStatusChange(e.target.value)}
        >
          {inventoryStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Input
          type="number"
          min={1}
          value={orderId}
          onChange={(e) => handleOrderIdChange(e.target.value)}
          placeholder="Filter by order ID"
        />
      </div>

      <div className="overflow-hidden rounded-xl border-2 border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-slate-700 dark:text-gray-300">
              <tr>
                <th className="px-6 py-4">eSIM</th>
                <th className="px-6 py-4">User</th>
                <th className="px-6 py-4">Order / Plan</th>
                <th className="px-6 py-4">Inventory</th>
                <th className="px-6 py-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={idx}>
                    {Array.from({ length: 5 }).map((__, cell) => (
                      <td key={cell} className="px-6 py-4">
                        <Skeleton className="h-4 w-24" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : profiles.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    No eSIM profiles match the current filters.
                  </td>
                </tr>
              ) : (
                profiles.map((profile) => (
                  <tr
                    key={profile.id}
                    className="hover:bg-gray-50 dark:hover:bg-slate-700/40"
                  >
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          #{profile.id}
                        </div>
                        <Badge variant={esimStatusVariant(profile.status)}>
                          {profile.status}
                        </Badge>
                        {profile.activation_code && (
                          <div className="text-xs font-mono text-gray-600">
                            {profile.activation_code}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {profile.user ? (
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {profile.user.email}
                          </div>
                          <div className="text-xs text-gray-600">
                            {profile.user.name || "—"}
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Unknown</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-900 dark:text-white">
                      <div>Order #{profile.order_id ?? "—"}</div>
                      <div className="text-xs text-gray-600">
                        Plan #{profile.plan_id ?? "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {profile.inventory_item_id ? (
                        <div className="space-y-1">
                          <div className="text-gray-900 dark:text-white">
                            Inventory #{profile.inventory_item_id}
                          </div>
                          <Badge variant="primary">Linked</Badge>
                          {profile.iccid && (
                            <div className="text-xs font-mono text-gray-600">
                              {profile.iccid}
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {dateFormatter.format(new Date(profile.created_at))}
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
