"use client";

import { apiUrl } from "@/lib/apiConfig";
import {
  Badge,
  Button,
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

interface AdminUserDetail {
  id: number;
  email: string | null;
  name?: string | null;
  created_at: string;
  last_login?: string | null;
  total_orders: number;
  total_spent_minor_units: number;
  last_order_at?: string | null;
  internal_notes?: string | null;
  open_tickets: number;
}

type SortField =
  | "created_at"
  | "last_login"
  | "total_orders"
  | "total_spent"
  | "last_order_at"
  | "open_tickets";
type SortOrder = "asc" | "desc";

const pageSize = 20;

const sortFieldOptions: { label: string; value: SortField }[] = [
  { label: "Newest", value: "created_at" },
  { label: "Last login", value: "last_login" },
  { label: "Total orders", value: "total_orders" },
  { label: "Lifetime value", value: "total_spent" },
  { label: "Last order", value: "last_order_at" },
  { label: "Open tickets", value: "open_tickets" },
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

const formatCurrency = (amountMinor: number) => {
  const value = amountMinor / 100;
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `$${value.toFixed(2)}`;
  }
};

const formatDate = (value?: string | null) => {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
};

const truncate = (value?: string | null, maxLength = 80) => {
  if (!value) return "Add note";
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}…`;
};

export default function AdminUsersPage() {
  const { showToast } = useToast();
  const [users, setUsers] = useState<AdminUserDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [noteDraft, setNoteDraft] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortField,
        sort_order: sortOrder,
      });
      if (search) params.set("q", search);

      const response = await fetch(
        apiUrl(`/admin/users?${params.toString()}`),
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
        throw new Error(error.detail || "Unable to load users");
      }

      const data: PaginatedResponse<AdminUserDetail> = await response.json();
      setUsers(data.items);
      setTotalPages(data.total_pages);
      setTotalItems(data.total);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load users", "error");
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, [page, sortField, sortOrder, search, showToast]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const startEditing = (user: AdminUserDetail) => {
    setEditingUserId(user.id);
    setNoteDraft(user.internal_notes || "");
  };

  const cancelEditing = () => {
    setEditingUserId(null);
    setNoteDraft("");
  };

  const saveNotes = async () => {
    if (!editingUserId) return;
    setSavingNotes(true);
    try {
      const response = await fetch(
        apiUrl(`/admin/users/${editingUserId}/notes`),
        {
          method: "PATCH",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
          body: JSON.stringify({ internal_notes: noteDraft || null }),
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to update notes");
      }

      showToast("Notes updated", "success");
      setEditingUserId(null);
      setNoteDraft("");
      fetchUsers();
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to update notes", "error");
    } finally {
      setSavingNotes(false);
    }
  };

  const stats = useMemo(() => {
    const totalRevenue = users.reduce(
      (sum, user) => sum + (user.total_spent_minor_units || 0),
      0,
    );
    const openTickets = users.reduce(
      (sum, user) => sum + (user.open_tickets || 0),
      0,
    );
    return { totalRevenue, openTickets };
  }, [users]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Users & CRM
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Search customers, review order history, and capture internal notes.
        </p>
      </div>

      <div className="grid gap-4 rounded-2xl border-2 border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-slate-800 md:grid-cols-3">
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">
            Total customers (filters)
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {totalItems}
          </p>
        </div>
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">
            Lifetime revenue (USD)
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {formatCurrency(stats.totalRevenue)}
          </p>
        </div>
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">
            Open tickets
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.openTickets}
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <SearchInput
            placeholder="Search by email or name..."
            onSearch={handleSearch}
            debounceMs={300}
          />
        </div>
        <Select
          value={sortField}
          onChange={(e) => {
            setSortField(e.target.value as SortField);
            setPage(1);
          }}
        >
          {sortFieldOptions.map((option) => (
            <option key={option.value} value={option.value}>
              Sort by: {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={sortOrder}
          onChange={(e) => {
            setSortOrder(e.target.value as SortOrder);
            setPage(1);
          }}
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
                <th className="px-6 py-4">User</th>
                <th className="px-6 py-4">Orders</th>
                <th className="px-6 py-4">Spend</th>
                <th className="px-6 py-4">Last activity</th>
                <th className="px-6 py-4">Tickets</th>
                <th className="px-6 py-4">Internal notes</th>
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
              ) : users.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    No users match the current filters.
                  </td>
                </tr>
              ) : (
                users.map((user) => {
                  const isEditing = editingUserId === user.id;
                  const lastActivity = user.last_login || user.last_order_at;
                  return (
                    <tr
                      key={user.id}
                      className="align-top hover:bg-gray-50 dark:hover:bg-slate-700/40"
                    >
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="font-semibold text-gray-900 dark:text-white">
                            {user.email || "Unknown"}
                          </div>
                          <div className="text-xs text-gray-600 dark:text-gray-300">
                            {user.name || "—"}
                          </div>
                          <div className="text-xs text-gray-500">
                            Joined {formatDate(user.created_at)}
                          </div>
                          <div className="text-xs text-gray-500">
                            Last login {formatDate(user.last_login)}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <p className="text-base font-semibold text-gray-900 dark:text-white">
                            {user.total_orders}
                          </p>
                          <p className="text-xs text-gray-500">
                            Last order {formatDate(user.last_order_at)}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-base font-semibold text-gray-900 dark:text-white">
                          {formatCurrency(user.total_spent_minor_units)}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="primary">
                          {formatDate(lastActivity)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <Badge
                          variant={
                            user.open_tickets > 0 ? "warning" : "default"
                          }
                        >
                          {user.open_tickets} open
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        {isEditing ? (
                          <div className="space-y-3">
                            <textarea
                              className="w-full rounded-lg border-2 border-gray-200 bg-white p-3 text-sm text-gray-900 shadow-inner focus:border-primary-500 focus:outline-none dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100"
                              rows={4}
                              value={noteDraft}
                              onChange={(e) => setNoteDraft(e.target.value)}
                              placeholder="Add context for support teams"
                            />
                            <div className="flex flex-wrap gap-3">
                              <Button
                                className="inline-flex items-center rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
                                disabled={savingNotes}
                                onClick={saveNotes}
                              >
                                {savingNotes ? "Saving..." : "Save"}
                              </Button>
                              <Button
                                className="inline-flex items-center rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-slate-700"
                                onClick={cancelEditing}
                                disabled={savingNotes}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <p className="text-sm text-gray-700 dark:text-gray-200">
                              {truncate(user.internal_notes)}
                            </p>
                            <Button
                              className="text-sm font-semibold text-primary-600 hover:text-primary-700"
                              onClick={() => startEditing(user)}
                            >
                              {user.internal_notes ? "Edit notes" : "Add notes"}
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {users.length > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
