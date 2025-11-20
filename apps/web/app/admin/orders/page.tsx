"use client";

import { apiUrl } from "@/lib/apiConfig";
import {
  Badge,
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

interface AdminPayment {
  id: number;
  provider: string;
  status: string;
  intent_id?: string | null;
  created_at: string;
}

interface AdminEsimProfile {
  id: number;
  status: string;
  activation_code?: string | null;
}

interface AdminOrder {
  id: number;
  status: string;
  currency: string;
  amount_minor_units: number;
  created_at: string;
  plan_id?: number | null;
  plan_snapshot?: { id?: number; name?: string } | null;
  user?: AdminUserSummary | null;
  payments: AdminPayment[];
  esim_profile?: AdminEsimProfile | null;
}

type SortField = "created_at" | "amount" | "status";
type SortOrder = "asc" | "desc";

type StatusOption = { label: string; value: string };

const pageSize = 20;

const orderStatusOptions: StatusOption[] = [
  { label: "All statuses", value: "all" },
  { label: "Created", value: "created" },
  { label: "Paid", value: "paid" },
  { label: "Failed", value: "failed" },
  { label: "Refunded", value: "refunded" },
];

const paymentStatusOptions: StatusOption[] = [
  { label: "Any payment", value: "all" },
  { label: "Succeeded", value: "succeeded" },
  { label: "Requires Action", value: "requires_action" },
  { label: "Failed", value: "failed" },
];

const sortFieldOptions: { label: string; value: SortField }[] = [
  { label: "Newest", value: "created_at" },
  { label: "Amount", value: "amount" },
  { label: "Status", value: "status" },
];

const sortOrderOptions: { label: string; value: SortOrder }[] = [
  { label: "Descending", value: "desc" },
  { label: "Ascending", value: "asc" },
];

const getAuthHeaders = (): HeadersInit => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const orderStatusVariant = (status: string) => {
  const normalized = status?.toLowerCase();
  if (normalized === "paid") return "success" as const;
  if (normalized === "failed") return "destructive" as const;
  if (normalized === "refunded") return "warning" as const;
  if (normalized === "created") return "primary" as const;
  return "default" as const;
};

const paymentStatusVariant = (status: string) => {
  const normalized = status?.toLowerCase();
  if (normalized === "succeeded") return "success" as const;
  if (normalized === "failed") return "destructive" as const;
  if (normalized === "requires_action") return "warning" as const;
  return "default" as const;
};

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export default function AdminOrdersPage() {
  const { showToast } = useToast();
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [search, setSearch] = useState("");
  const [orderStatus, setOrderStatus] = useState("all");
  const [paymentStatus, setPaymentStatus] = useState("all");
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const formatAmount = useCallback(
    (amountMinor: number, currencyCode: string) => {
      const value = amountMinor / 100;
      try {
        return new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: currencyCode || "USD",
        }).format(value);
      } catch {
        return currencyFormatter.format(value);
      }
    },
    [],
  );

  const formatDate = useCallback((value?: string | null) => {
    if (!value) return "—";
    try {
      return dateFormatter.format(new Date(value));
    } catch {
      return value;
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortField,
        sort_order: sortOrder,
      });
      if (search) params.set("user_q", search);
      if (orderStatus !== "all") params.set("order_status", orderStatus);
      if (paymentStatus !== "all") params.set("payment_status", paymentStatus);

      const response = await fetch(
        apiUrl(`/admin/orders?${params.toString()}`),
        {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to load orders");
      }

      const data: PaginatedResponse<AdminOrder> = await response.json();
      setOrders(data.items);
      setTotalPages(data.total_pages);
      setTotalItems(data.total);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load orders", "error");
      setOrders([]);
    } finally {
      setLoading(false);
    }
  }, [
    page,
    sortField,
    sortOrder,
    search,
    orderStatus,
    paymentStatus,
    showToast,
  ]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const handleOrderStatusChange = (value: string) => {
    setOrderStatus(value);
    setPage(1);
  };

  const handlePaymentStatusChange = (value: string) => {
    setPaymentStatus(value);
    setPage(1);
  };

  const handleSortFieldChange = (value: SortField) => {
    setSortField(value);
    setPage(1);
  };

  const handleSortOrderChange = (value: SortOrder) => {
    setSortOrder(value);
    setPage(1);
  };

  const renderPayments = (order: AdminOrder) => {
    if (!order.payments?.length) {
      return <span className="text-sm text-gray-500">No payments</span>;
    }

    const latest = order.payments[0];
    return (
      <div className="space-y-1">
        <Badge variant={paymentStatusVariant(latest.status)}>
          {latest.status}
        </Badge>
        <div className="text-xs text-gray-600">
          {latest.provider}
          {latest.intent_id ? ` · ${latest.intent_id}` : ""}
        </div>
      </div>
    );
  };

  const renderEsim = (order: AdminOrder) => {
    if (!order.esim_profile) {
      return <span className="text-sm text-gray-500">Unassigned</span>;
    }
    return (
      <div className="space-y-1">
        <Badge variant="accent">{order.esim_profile.status}</Badge>
        {order.esim_profile.activation_code && (
          <div className="text-xs text-gray-600">
            {order.esim_profile.activation_code}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Orders
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Search, filter, and audit orders across statuses and payment states.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <SearchInput
            placeholder="Search by customer email or name..."
            onSearch={handleSearch}
            debounceMs={300}
          />
        </div>
        <Select
          value={orderStatus}
          onChange={(e) => handleOrderStatusChange(e.target.value)}
        >
          {orderStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={paymentStatus}
          onChange={(e) => handlePaymentStatusChange(e.target.value)}
        >
          {paymentStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={sortField}
          onChange={(e) => handleSortFieldChange(e.target.value as SortField)}
        >
          {sortFieldOptions.map((option) => (
            <option key={option.value} value={option.value}>
              Sort by: {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={sortOrder}
          onChange={(e) => handleSortOrderChange(e.target.value as SortOrder)}
        >
          {sortOrderOptions.map((option) => (
            <option key={option.value} value={option.value}>
              Order: {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="overflow-hidden rounded-xl border-2 border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-slate-700 dark:text-gray-300">
              <tr>
                <th className="px-6 py-4">Order</th>
                <th className="px-6 py-4">User</th>
                <th className="px-6 py-4">Plan</th>
                <th className="px-6 py-4">Payments</th>
                <th className="px-6 py-4">eSIM</th>
                <th className="px-6 py-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={idx}>
                    {Array.from({ length: 6 }).map((__, cell) => (
                      <td key={cell} className="px-6 py-4">
                        <Skeleton className="h-4 w-24" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : orders.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    No orders match the current filters.
                  </td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr
                    key={order.id}
                    className="hover:bg-gray-50 dark:hover:bg-slate-700/40"
                  >
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          #{order.id}
                        </div>
                        <Badge variant={orderStatusVariant(order.status)}>
                          {order.status}
                        </Badge>
                        <div className="text-sm text-gray-600 dark:text-gray-300">
                          {formatAmount(
                            order.amount_minor_units,
                            order.currency,
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {order.user ? (
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {order.user.email}
                          </div>
                          <div className="text-xs text-gray-600">
                            {order.user.name || "—"}
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Unknown</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-gray-900 dark:text-white">
                        {order.plan_snapshot?.name ||
                          `Plan #${order.plan_id ?? "—"}`}
                      </div>
                      <div className="text-xs text-gray-500">
                        ID: {order.plan_snapshot?.id || order.plan_id || "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4">{renderPayments(order)}</td>
                    <td className="px-6 py-4">{renderEsim(order)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {formatDate(order.created_at)}
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
