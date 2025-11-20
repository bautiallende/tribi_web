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

interface AdminPayment {
  id: number;
  provider: string;
  status: string;
  intent_id?: string | null;
  order_id: number;
  created_at: string;
  order_amount_minor_units: number;
  order_currency?: string | null;
}

type SortOrder = "asc" | "desc";

const pageSize = 20;

const providerOptions = [
  { label: "All providers", value: "all" },
  { label: "Stripe", value: "stripe" },
  { label: "Mercado Pago", value: "mercado_pago" },
  { label: "Mock", value: "mock" },
];

const paymentStatusOptions = [
  { label: "Any status", value: "all" },
  { label: "Succeeded", value: "succeeded" },
  { label: "Requires Action", value: "requires_action" },
  { label: "Failed", value: "failed" },
];

const sortOrderOptions = [
  { label: "Newest first", value: "desc" },
  { label: "Oldest first", value: "asc" },
];

const getAuthHeaders = (): HeadersInit => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const paymentStatusVariant = (status: string) => {
  const normalized = status?.toLowerCase();
  if (normalized === "succeeded") return "success" as const;
  if (normalized === "failed") return "destructive" as const;
  if (normalized === "requires_action") return "warning" as const;
  return "default" as const;
};

const currencyFormatter = (
  currency: string | null | undefined,
  amount: number,
) => {
  const value = amount / 100;
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
    }).format(value);
  } catch {
    return `${currency || "USD"} ${value.toFixed(2)}`;
  }
};

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});

export default function AdminPaymentsPage() {
  const { showToast } = useToast();
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [search, setSearch] = useState("");
  const [provider, setProvider] = useState("all");
  const [status, setStatus] = useState("all");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const fetchPayments = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_order: sortOrder,
      });
      if (search) params.set("intent_q", search);
      if (provider !== "all") params.set("provider", provider);
      if (status !== "all") params.set("payment_status", status);

      const response = await fetch(
        apiUrl(`/admin/payments?${params.toString()}`),
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
        throw new Error(err.detail || "Unable to load payments");
      }

      const data: PaginatedResponse<AdminPayment> = await response.json();
      setPayments(data.items);
      setTotalItems(data.total);
      setTotalPages(data.total_pages);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load payments", "error");
      setPayments([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, provider, status, sortOrder, showToast]);

  useEffect(() => {
    fetchPayments();
  }, [fetchPayments]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const handleProviderChange = (value: string) => {
    setProvider(value);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatus(value);
    setPage(1);
  };

  const handleSortOrderChange = (value: SortOrder) => {
    setSortOrder(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Payments
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Review provider activity, statuses, and reconciliation information.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="md:col-span-2">
          <SearchInput
            placeholder="Search by intent ID..."
            onSearch={handleSearch}
            debounceMs={300}
          />
        </div>
        <Select
          value={provider}
          onChange={(e) => handleProviderChange(e.target.value)}
        >
          {providerOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={status}
          onChange={(e) => handleStatusChange(e.target.value)}
        >
          {paymentStatusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={sortOrder}
          onChange={(e) => handleSortOrderChange(e.target.value as SortOrder)}
        >
          {sortOrderOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="overflow-hidden rounded-xl border-2 border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-slate-700 dark:text-gray-300">
              <tr>
                <th className="px-6 py-4">Payment</th>
                <th className="px-6 py-4">Order</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">Intent</th>
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
              ) : payments.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    No payments found for the current filters.
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr
                    key={payment.id}
                    className="hover:bg-gray-50 dark:hover:bg-slate-700/40"
                  >
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          #{payment.id}
                        </div>
                        <Badge variant={paymentStatusVariant(payment.status)}>
                          {payment.status}
                        </Badge>
                        <div className="text-xs text-gray-500">
                          {payment.provider}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-900 dark:text-white">
                      Order #{payment.order_id}
                    </td>
                    <td className="px-6 py-4 text-gray-900 dark:text-white">
                      {currencyFormatter(
                        payment.order_currency,
                        payment.order_amount_minor_units,
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {payment.intent_id ? (
                        <span className="font-mono text-xs text-gray-800 dark:text-gray-200">
                          {payment.intent_id}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {dateFormatter.format(new Date(payment.created_at))}
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
