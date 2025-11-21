"use client";

import { apiUrl } from "@/lib/apiConfig";
import {
  Badge,
  Button,
  Input,
  Pagination,
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

interface AdminUserSummary {
  id: number;
  email: string | null;
  name?: string | null;
}

interface SupportTicket {
  id: number;
  user: AdminUserSummary;
  order_id?: number | null;
  status: string;
  priority: string;
  subject: string;
  description?: string | null;
  internal_notes?: string | null;
  created_by?: string | null;
  updated_by?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

interface TicketDraftState {
  status: string;
  priority: string;
  internal_notes: string;
}

interface UserSuggestion extends AdminUserSummary {
  total_orders?: number;
  total_spent_minor_units?: number;
  last_order_at?: string | null;
}

type DraftMap = Record<number, TicketDraftState>;

const pageSize = 20;

const statusOptions = [
  { label: "All statuses", value: "all" },
  { label: "Open", value: "open" },
  { label: "In progress", value: "in_progress" },
  { label: "Resolved", value: "resolved" },
  { label: "Archived", value: "archived" },
];

const priorityOptions = [
  { label: "Any priority", value: "all" },
  { label: "Low", value: "low" },
  { label: "Normal", value: "normal" },
  { label: "High", value: "high" },
];

const getAuthHeaders = (): HeadersInit => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
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

const statusVariant = (status: string) => {
  const normalized = status?.toLowerCase();
  if (normalized === "resolved") return "success" as const;
  if (normalized === "in_progress") return "primary" as const;
  if (normalized === "archived") return "default" as const;
  return "warning" as const;
};

const priorityVariant = (priority: string) => {
  const normalized = priority?.toLowerCase();
  if (normalized === "high") return "destructive" as const;
  if (normalized === "low") return "default" as const;
  return "accent" as const;
};

export default function SupportTicketsPage() {
  const { showToast } = useToast();
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [userIdFilter, setUserIdFilter] = useState("");
  const [orderIdFilter, setOrderIdFilter] = useState("");
  const [ticketDrafts, setTicketDrafts] = useState<DraftMap>({});
  const [savingTicketId, setSavingTicketId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    userId: "",
    orderId: "",
    subject: "",
    description: "",
    priority: "normal",
  });
  const [userQuery, setUserQuery] = useState("");
  const [userSuggestions, setUserSuggestions] = useState<UserSuggestion[]>([]);
  const [userLookupLoading, setUserLookupLoading] = useState(false);
  const [userLookupError, setUserLookupError] = useState<string | null>(null);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (statusFilter !== "all") params.set("status_filter", statusFilter);
      if (priorityFilter !== "all") params.set("priority", priorityFilter);
      if (userIdFilter) params.set("user_id", userIdFilter);
      if (orderIdFilter) params.set("order_id", orderIdFilter);

      const response = await fetch(
        apiUrl(`/admin/support/tickets?${params.toString()}`),
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
        throw new Error(error.detail || "Unable to load tickets");
      }

      const data: PaginatedResponse<SupportTicket> = await response.json();
      setTickets(data.items);
      setTotalPages(data.total_pages);

      const drafts: DraftMap = {};
      data.items.forEach((ticket) => {
        drafts[ticket.id] = {
          status: ticket.status,
          priority: ticket.priority,
          internal_notes: ticket.internal_notes || "",
        };
      });
      setTicketDrafts(drafts);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load tickets", "error");
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [
    page,
    statusFilter,
    priorityFilter,
    userIdFilter,
    orderIdFilter,
    showToast,
  ]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    const term = userQuery.trim();
    if (term.length < 2) {
      setUserSuggestions([]);
      setUserLookupError(null);
      setUserLookupLoading(false);
      return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(async () => {
      setUserLookupLoading(true);
      try {
        const params = new URLSearchParams({
          q: term,
          page: "1",
          page_size: "5",
        });
        const response = await fetch(
          apiUrl(`/admin/users?${params.toString()}`),
          {
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
              ...getAuthHeaders(),
            },
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || "Unable to search users");
        }

        const data: PaginatedResponse<UserSuggestion> = await response.json();
        setUserSuggestions(data.items);
        setUserLookupError(
          data.items.length === 0 ? "No matching users" : null,
        );
      } catch (error: any) {
        if (error.name === "AbortError") return;
        console.error(error);
        setUserLookupError(error.message || "Failed to search users");
        setUserSuggestions([]);
      } finally {
        setUserLookupLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [userQuery]);

  const handleDraftChange = (
    id: number,
    field: keyof TicketDraftState,
    value: string,
  ) => {
    setTicketDrafts((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [field]: value,
      },
    }));
  };

  const saveTicket = async (ticketId: number) => {
    const draft = ticketDrafts[ticketId];
    if (!draft) return;
    setSavingTicketId(ticketId);
    try {
      const response = await fetch(
        apiUrl(`/admin/support/tickets/${ticketId}`),
        {
          method: "PATCH",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
          body: JSON.stringify({
            status: draft.status,
            priority: draft.priority,
            internal_notes: draft.internal_notes || null,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to update ticket");
      }

      showToast("Ticket updated", "success");
      fetchTickets();
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to update ticket", "error");
    } finally {
      setSavingTicketId(null);
    }
  };

  const handleSelectUser = (suggestion: UserSuggestion) => {
    setCreateForm((prev) => ({ ...prev, userId: suggestion.id.toString() }));
    setUserQuery(suggestion.email || `User #${suggestion.id}`);
    setUserSuggestions([]);
    setUserLookupError(null);
  };

  const clearSelectedUser = () => {
    setCreateForm((prev) => ({ ...prev, userId: "" }));
    setUserQuery("");
    setUserSuggestions([]);
    setUserLookupError(null);
  };

  const handleCreateTicket = async () => {
    if (!createForm.userId || !createForm.subject.trim()) {
      showToast("User ID and subject are required", "warning");
      return;
    }

    setCreating(true);
    try {
      const payload = {
        user_id: Number(createForm.userId),
        order_id: createForm.orderId ? Number(createForm.orderId) : undefined,
        subject: createForm.subject.trim(),
        description: createForm.description.trim() || undefined,
        priority: createForm.priority,
      };

      const response = await fetch(apiUrl("/admin/support/tickets"), {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to create ticket");
      }

      showToast("Ticket created", "success");
      setCreateForm({
        userId: "",
        orderId: "",
        subject: "",
        description: "",
        priority: "normal",
      });
      setPage(1);
      fetchTickets();
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to create ticket", "error");
    } finally {
      setCreating(false);
    }
  };

  const stats = useMemo(() => {
    const open = tickets.filter((ticket) => ticket.status === "open").length;
    const inProgress = tickets.filter(
      (ticket) => ticket.status === "in_progress",
    ).length;
    const resolved = tickets.filter(
      (ticket) => ticket.status === "resolved",
    ).length;
    return { open, inProgress, resolved };
  }, [tickets]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Support Tickets
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage inbound issues, update status/priority, and document outcomes.
        </p>
      </div>

      <div className="grid gap-4 rounded-2xl border-2 border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-slate-800 md:grid-cols-3">
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">
            Open tickets
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.open}
          </p>
        </div>
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">
            In progress
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.inProgress}
          </p>
        </div>
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">
            Resolved (this page)
          </p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
            {stats.resolved}
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select
          value={priorityFilter}
          onChange={(e) => {
            setPriorityFilter(e.target.value);
            setPage(1);
          }}
        >
          {priorityOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Input
          type="number"
          placeholder="Filter by user ID"
          value={userIdFilter}
          onChange={(e) => {
            setUserIdFilter(e.target.value);
            setPage(1);
          }}
        />
        <Input
          type="number"
          placeholder="Filter by order ID"
          value={orderIdFilter}
          onChange={(e) => {
            setOrderIdFilter(e.target.value);
            setPage(1);
          }}
        />
        <Button
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-slate-700"
          onClick={() => {
            setStatusFilter("all");
            setPriorityFilter("all");
            setUserIdFilter("");
            setOrderIdFilter("");
            setPage(1);
          }}
        >
          Clear filters
        </Button>
      </div>

      <div className="rounded-2xl border-2 border-dashed border-gray-300 bg-white p-6 dark:border-gray-600 dark:bg-slate-800">
        <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
          Create ticket
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">
                Find user *
              </p>
              {createForm.userId && (
                <button
                  type="button"
                  onClick={clearSelectedUser}
                  className="text-xs font-semibold text-primary-600 hover:text-primary-700"
                >
                  Clear selection
                </button>
              )}
            </div>
            <Input
              placeholder="Search by email or name"
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
            />
            {userLookupLoading && (
              <p className="text-xs text-gray-500">Searching users…</p>
            )}
            {!userLookupLoading && userLookupError && (
              <p className="text-xs text-red-600">{userLookupError}</p>
            )}
            {userSuggestions.length > 0 && (
              <ul className="divide-y divide-gray-200 overflow-hidden rounded-lg border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
                {userSuggestions.map((suggestion) => (
                  <li
                    key={suggestion.id}
                    className="cursor-pointer bg-gray-50/70 px-4 py-3 transition hover:bg-primary-50 dark:bg-slate-800 dark:hover:bg-slate-700"
                    onClick={() => handleSelectUser(suggestion)}
                  >
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {suggestion.email || `User #${suggestion.id}`}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-300">
                      #{suggestion.id}
                      {suggestion.name ? ` · ${suggestion.name}` : ""}
                      {typeof suggestion.total_orders === "number"
                        ? ` · ${suggestion.total_orders} orders`
                        : ""}
                    </p>
                  </li>
                ))}
              </ul>
            )}
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Selected user ID: {createForm.userId || "None"}
            </div>
            <Input
              type="number"
              placeholder="Or enter user ID manually"
              value={createForm.userId}
              onChange={(e) =>
                setCreateForm((prev) => ({ ...prev, userId: e.target.value }))
              }
            />
          </div>
          <Input
            type="number"
            placeholder="Order ID (optional)"
            value={createForm.orderId}
            onChange={(e) =>
              setCreateForm((prev) => ({ ...prev, orderId: e.target.value }))
            }
          />
          <Input
            placeholder="Subject *"
            value={createForm.subject}
            onChange={(e) =>
              setCreateForm((prev) => ({ ...prev, subject: e.target.value }))
            }
          />
          <Select
            value={createForm.priority}
            onChange={(e) =>
              setCreateForm((prev) => ({ ...prev, priority: e.target.value }))
            }
          >
            {priorityOptions
              .filter((option) => option.value !== "all")
              .map((option) => (
                <option key={option.value} value={option.value}>
                  Priority: {option.label}
                </option>
              ))}
          </Select>
        </div>
        <textarea
          className="mt-4 w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-sm text-gray-900 focus:border-primary-500 focus:outline-none dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100"
          rows={4}
          placeholder="Description"
          value={createForm.description}
          onChange={(e) =>
            setCreateForm((prev) => ({ ...prev, description: e.target.value }))
          }
        />
        <div className="mt-4 flex justify-end">
          <Button
            className="inline-flex items-center rounded-md bg-primary-600 px-6 py-2 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
            onClick={handleCreateTicket}
            disabled={creating}
          >
            {creating ? "Creating..." : "Create ticket"}
          </Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border-2 border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-slate-700 dark:text-gray-300">
              <tr>
                <th className="px-6 py-4">Ticket</th>
                <th className="px-6 py-4">User / Order</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Priority</th>
                <th className="px-6 py-4">Notes</th>
                <th className="px-6 py-4 text-right">Actions</th>
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
              ) : tickets.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-gray-500"
                  >
                    No tickets match the current filters.
                  </td>
                </tr>
              ) : (
                tickets.map((ticket) => {
                  const draft = ticketDrafts[ticket.id];
                  return (
                    <tr
                      key={ticket.id}
                      className="align-top hover:bg-gray-50 dark:hover:bg-slate-700/40"
                    >
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="font-semibold text-gray-900 dark:text-white">
                            #{ticket.id} · {ticket.subject}
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-300">
                            Created {formatDate(ticket.created_at)}
                          </p>
                          {ticket.resolved_at && (
                            <p className="text-xs text-gray-500">
                              Resolved {formatDate(ticket.resolved_at)}
                            </p>
                          )}
                          {ticket.description && (
                            <p className="text-xs text-gray-500">
                              {ticket.description}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <p className="font-medium text-gray-900 dark:text-white">
                            {ticket.user?.email || "Unknown"}
                          </p>
                          <p className="text-xs text-gray-500">
                            User #{ticket.user?.id}
                            {ticket.user?.name ? ` · ${ticket.user.name}` : ""}
                          </p>
                          <p className="text-xs text-gray-500">
                            {ticket.order_id
                              ? `Order #${ticket.order_id}`
                              : "No order"}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Select
                          value={draft?.status || ticket.status}
                          onChange={(e) =>
                            handleDraftChange(
                              ticket.id,
                              "status",
                              e.target.value,
                            )
                          }
                        >
                          {statusOptions
                            .filter((option) => option.value !== "all")
                            .map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                        </Select>
                        <div className="mt-2">
                          <Badge
                            variant={statusVariant(
                              draft?.status || ticket.status,
                            )}
                          >
                            {draft?.status || ticket.status}
                          </Badge>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Select
                          value={draft?.priority || ticket.priority}
                          onChange={(e) =>
                            handleDraftChange(
                              ticket.id,
                              "priority",
                              e.target.value,
                            )
                          }
                        >
                          {priorityOptions
                            .filter((option) => option.value !== "all")
                            .map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                        </Select>
                        <div className="mt-2">
                          <Badge
                            variant={priorityVariant(
                              draft?.priority || ticket.priority,
                            )}
                          >
                            {draft?.priority || ticket.priority}
                          </Badge>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <textarea
                          className="w-full rounded-lg border-2 border-gray-200 bg-white p-3 text-sm text-gray-900 focus:border-primary-500 focus:outline-none dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100"
                          rows={4}
                          value={
                            draft?.internal_notes ?? ticket.internal_notes ?? ""
                          }
                          onChange={(e) =>
                            handleDraftChange(
                              ticket.id,
                              "internal_notes",
                              e.target.value,
                            )
                          }
                          placeholder="Add internal notes"
                        />
                        <p className="mt-2 text-xs text-gray-500">
                          Last updated {formatDate(ticket.updated_at)} by{" "}
                          {ticket.updated_by || "unknown"}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button
                          className="inline-flex items-center rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
                          onClick={() => saveTicket(ticket.id)}
                          disabled={savingTicketId === ticket.id}
                        >
                          {savingTicketId === ticket.id ? "Saving..." : "Save"}
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {tickets.length > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
