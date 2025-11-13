"use client";

import { useState, useEffect, useCallback } from "react";
import { SearchInput, Pagination, Dialog, useToast, Skeleton } from "@tribi/ui";

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

type SortField = 'name' | 'id';
type SortOrder = 'asc' | 'desc';

export default function CarriersAdmin() {
  const { showToast } = useToast();
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [showModal, setShowModal] = useState(false);
  const [editingCarrier, setEditingCarrier] = useState<Carrier | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Carrier | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState({ name: "" });
  const [formErrors, setFormErrors] = useState<{ name?: string }>({});

  const pageSize = 20;

  // Fetch carriers
  const fetchCarriers = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortField,
        sort_order: sortOrder,
        ...(search && { q: search }),
      });

      const response = await fetch(
        `http://localhost:8000/admin/carriers?${params}`,
        { credentials: "include" }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch carriers');
      }

      const data: PaginatedResponse = await response.json();
      setCarriers(data.items);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (error) {
      showToast("Failed to load carriers", "error");
      setCarriers([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, sortField, sortOrder, showToast]);

  useEffect(() => {
    fetchCarriers();
  }, [fetchCarriers]);

  // Sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
    setPage(1);
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return '↕️';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  // Search
  const handleSearch = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  // Validate
  const validateForm = () => {
    const errors: { name?: string } = {};

    if (!formData.name.trim()) {
      errors.name = "Carrier name is required";
    } else if (formData.name.length < 2) {
      errors.name = "Name must be at least 2 characters";
    } else if (formData.name.length > 100) {
      errors.name = "Name must be less than 100 characters";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);

    try {
      const url = editingCarrier
        ? `http://localhost:8000/admin/carriers/${editingCarrier.id}`
        : "http://localhost:8000/admin/carriers";
      
      const method = editingCarrier ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: formData.name.trim() }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save carrier");
      }

      showToast(
        `Carrier ${editingCarrier ? "updated" : "created"} successfully`,
        "success"
      );
      
      setShowModal(false);
      fetchCarriers();
      resetForm();
    } catch (error: any) {
      showToast(error.message || "Failed to save carrier", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete
  const handleDelete = async () => {
    if (!deleteTarget) return;

    setIsSubmitting(true);

    try {
      const response = await fetch(
        `http://localhost:8000/admin/carriers/${deleteTarget.id}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete carrier");
      }

      showToast("Carrier deleted successfully", "success");
      setDeleteTarget(null);
      fetchCarriers();
    } catch (error: any) {
      showToast(error.message || "Failed to delete carrier", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Modal handlers
  const openCreateModal = () => {
    resetForm();
    setEditingCarrier(null);
    setShowModal(true);
  };

  const openEditModal = (carrier: Carrier) => {
    setFormData({ name: carrier.name });
    setEditingCarrier(carrier);
    setFormErrors({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    resetForm();
  };

  const resetForm = () => {
    setFormData({ name: "" });
    setFormErrors({});
    setEditingCarrier(null);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Carriers
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage eSIM network carriers
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition-colors"
        >
          + Add Carrier
        </button>
      </div>

      {/* Search and Stats */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <SearchInput
          placeholder="Search carriers by name..."
          onSearch={handleSearch}
          debounceMs={300}
          className="w-full sm:max-w-md"
        />
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Total: <span className="font-semibold">{total}</span> carriers
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border-2 border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-slate-700 border-b-2 border-gray-200 dark:border-gray-600">
              <tr>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('id')}
                    className="flex items-center gap-2 font-semibold text-gray-700 dark:text-gray-200 hover:text-primary-600 transition-colors"
                  >
                    ID {getSortIcon('id')}
                  </button>
                </th>
                <th className="px-6 py-4 text-left">
                  <button
                    onClick={() => handleSort('name')}
                    className="flex items-center gap-2 font-semibold text-gray-700 dark:text-gray-200 hover:text-primary-600 transition-colors"
                  >
                    Carrier Name {getSortIcon('name')}
                  </button>
                </th>
                <th className="px-6 py-4 text-right font-semibold text-gray-700 dark:text-gray-200">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4">
                      <Skeleton className="h-4 w-12" />
                    </td>
                    <td className="px-6 py-4">
                      <Skeleton className="h-4 w-48" />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-end gap-2">
                        <Skeleton className="h-8 w-16" />
                        <Skeleton className="h-8 w-16" />
                      </div>
                    </td>
                  </tr>
                ))
              ) : carriers.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-12 text-center">
                    <div className="text-gray-500 dark:text-gray-400">
                      <div className="text-4xl mb-2">📡</div>
                      <p className="text-lg font-medium">No carriers found</p>
                      <p className="text-sm mt-1">
                        {search ? 'Try a different search' : 'Add your first carrier to get started'}
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                carriers.map((carrier) => (
                  <tr
                    key={carrier.id}
                    className="hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <span className="text-gray-600 dark:text-gray-400 font-mono text-sm">
                        #{carrier.id}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-900 dark:text-white font-medium">
                        {carrier.name}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => openEditModal(carrier)}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => setDeleteTarget(carrier)}
                          className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium text-sm transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="mt-6">
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
          totalItems={total}
          itemsPerPage={pageSize}
        />
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={closeModal}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-md w-full p-6">
              <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                {editingCarrier ? "Edit Carrier" : "Create Carrier"}
              </h3>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Carrier Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="w-full px-3 py-2 border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
                      placeholder="AT&T, Vodafone, Orange..."
                    />
                    {formErrors.name && (
                      <p className="text-red-600 text-sm mt-1">{formErrors.name}</p>
                    )}
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={closeModal}
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-semibold transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? "Saving..." : editingCarrier ? "Update" : "Create"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}

      {/* Delete Dialog */}
      <Dialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Carrier"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone and may affect existing plans.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isSubmitting}
      />
    </div>
  );
}
