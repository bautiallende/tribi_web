"use client";

import { useState, useEffect } from "react";

interface Carrier {
  id: number;
  name: string;
}

interface PaginatedResponse {
  items: Carrier[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function CarriersAdmin() {
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [editingCarrier, setEditingCarrier] = useState<Carrier | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Carrier | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

  // Form state
  const [formData, setFormData] = useState({ name: "" });
  const [formErrors, setFormErrors] = useState<{ name?: string }>({});

  const pageSize = 20;

  // Fetch carriers
  const fetchCarriers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...(search && { q: search }),
      });

      const response = await fetch(
        `http://localhost:8000/admin/carriers?${params}`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) throw new Error("Failed to fetch carriers");

      const data: PaginatedResponse = await response.json();
      setCarriers(data.items);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (error) {
      showToast("Failed to load carriers", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCarriers();
  }, [page, search]);

  // Toast notification
  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Validate form
  const validateForm = () => {
    const errors: { name?: string } = {};

    if (!formData.name.trim()) {
      errors.name = "Carrier name is required";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Open create modal
  const handleCreate = () => {
    setEditingCarrier(null);
    setFormData({ name: "" });
    setFormErrors({});
    setShowModal(true);
  };

  // Open edit modal
  const handleEdit = (carrier: Carrier) => {
    setEditingCarrier(carrier);
    setFormData({ name: carrier.name });
    setFormErrors({});
    setShowModal(true);
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      const url = editingCarrier
        ? `http://localhost:8000/admin/carriers/${editingCarrier.id}`
        : "http://localhost:8000/admin/carriers";

      const method = editingCarrier ? "PUT" : "POST";

      // Optimistic update
      if (editingCarrier) {
        setCarriers((prev) =>
          prev.map((c) =>
            c.id === editingCarrier.id ? { ...c, name: formData.name } : c
          )
        );
      }

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save carrier");
      }

      const savedCarrier: Carrier = await response.json();

      // Update with real data
      if (editingCarrier) {
        setCarriers((prev) =>
          prev.map((c) => (c.id === savedCarrier.id ? savedCarrier : c))
        );
      } else {
        fetchCarriers();
      }

      showToast(
        editingCarrier ? "Carrier updated" : "Carrier created",
        "success"
      );
      setShowModal(false);
    } catch (error: any) {
      showToast(error.message, "error");
      if (editingCarrier) {
        fetchCarriers();
      }
    }
  };

  // Delete carrier
  const handleDelete = async (carrier: Carrier) => {
    try {
      // Optimistic delete
      setCarriers((prev) => prev.filter((c) => c.id !== carrier.id));
      setDeleteConfirm(null);

      const response = await fetch(
        `http://localhost:8000/admin/carriers/${carrier.id}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete carrier");
      }

      showToast("Carrier deleted", "success");
      fetchCarriers();
    } catch (error: any) {
      showToast(error.message, "error");
      fetchCarriers();
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Carriers</h2>
        <button
          onClick={handleCreate}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          + Add Carrier
        </button>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by name..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Name
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {loading ? (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : carriers.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-gray-500">
                  No carriers found
                </td>
              </tr>
            ) : (
              carriers.map((carrier) => (
                <tr key={carrier.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {carrier.id}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    {carrier.name}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <button
                      onClick={() => handleEdit(carrier)}
                      className="mr-3 text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(carrier)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {carriers.length} of {total} carriers
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-700">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-lg border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-xl font-bold text-gray-900">
              {editingCarrier ? "Edit Carrier" : "Add Carrier"}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Carrier Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                  placeholder="AT&T"
                />
                {formErrors.name && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                >
                  {editingCarrier ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-xl font-bold text-gray-900">
              Delete Carrier
            </h3>
            <p className="mb-6 text-gray-600">
              Are you sure you want to delete{" "}
              <span className="font-semibold">{deleteConfirm.name}</span>? This
              action cannot be undone and will fail if any plans reference this
              carrier.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 rounded-lg bg-white px-6 py-4 shadow-lg">
          <div className="flex items-center gap-3">
            {toast.type === "success" ? (
              <svg
                className="h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : (
              <svg
                className="h-5 w-5 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            )}
            <p className="text-sm font-medium text-gray-900">{toast.message}</p>
          </div>
        </div>
      )}
    </div>
  );
}
