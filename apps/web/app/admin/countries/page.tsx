"use client";

import { useState, useEffect } from "react";

interface Country {
  id: number;
  iso2: string;
  name: string;
}

interface PaginatedResponse {
  items: Country[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function CountriesAdmin() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [editingCountry, setEditingCountry] = useState<Country | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Country | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

  // Form state
  const [formData, setFormData] = useState({ iso2: "", name: "" });
  const [formErrors, setFormErrors] = useState<{ iso2?: string; name?: string }>(
    {}
  );

  const pageSize = 20;

  // Fetch countries
  const fetchCountries = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...(search && { q: search }),
      });

      const response = await fetch(
        `http://localhost:8000/admin/countries?${params}`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) throw new Error("Failed to fetch countries");

      const data: PaginatedResponse = await response.json();
      setCountries(data.items);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (error) {
      showToast("Failed to load countries", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCountries();
  }, [page, search]);

  // Toast notification
  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Validate form
  const validateForm = () => {
    const errors: { iso2?: string; name?: string } = {};

    if (!formData.iso2.trim()) {
      errors.iso2 = "ISO2 code is required";
    } else if (!/^[A-Za-z]{2}$/.test(formData.iso2)) {
      errors.iso2 = "ISO2 must be exactly 2 letters";
    }

    if (!formData.name.trim()) {
      errors.name = "Country name is required";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Open create modal
  const handleCreate = () => {
    setEditingCountry(null);
    setFormData({ iso2: "", name: "" });
    setFormErrors({});
    setShowModal(true);
  };

  // Open edit modal
  const handleEdit = (country: Country) => {
    setEditingCountry(country);
    setFormData({ iso2: country.iso2, name: country.name });
    setFormErrors({});
    setShowModal(true);
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      const url = editingCountry
        ? `http://localhost:8000/admin/countries/${editingCountry.id}`
        : "http://localhost:8000/admin/countries";

      const method = editingCountry ? "PUT" : "POST";

      // Optimistic update
      if (editingCountry) {
        setCountries((prev) =>
          prev.map((c) =>
            c.id === editingCountry.id
              ? { ...c, iso2: formData.iso2.toUpperCase(), name: formData.name }
              : c
          )
        );
      } else {
        // For create, we'll add after success to get the real ID
      }

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save country");
      }

      const savedCountry: Country = await response.json();

      // Update with real data
      if (editingCountry) {
        setCountries((prev) =>
          prev.map((c) => (c.id === savedCountry.id ? savedCountry : c))
        );
      } else {
        // Refresh to get accurate pagination
        fetchCountries();
      }

      showToast(
        editingCountry ? "Country updated" : "Country created",
        "success"
      );
      setShowModal(false);
    } catch (error: any) {
      showToast(error.message, "error");
      // Revert optimistic update on error
      if (editingCountry) {
        fetchCountries();
      }
    }
  };

  // Delete country
  const handleDelete = async (country: Country) => {
    try {
      // Optimistic delete
      setCountries((prev) => prev.filter((c) => c.id !== country.id));
      setDeleteConfirm(null);

      const response = await fetch(
        `http://localhost:8000/admin/countries/${country.id}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete country");
      }

      showToast("Country deleted", "success");
      // Refresh to update pagination
      fetchCountries();
    } catch (error: any) {
      showToast(error.message, "error");
      // Revert on error
      fetchCountries();
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Countries</h2>
        <button
          onClick={handleCreate}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          + Add Country
        </button>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by name or ISO2..."
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
                ISO2
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
            ) : countries.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-gray-500">
                  No countries found
                </td>
              </tr>
            ) : (
              countries.map((country) => (
                <tr key={country.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    {country.iso2}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-700">
                    {country.name}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                    <button
                      onClick={() => handleEdit(country)}
                      className="mr-3 text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(country)}
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
            Showing {countries.length} of {total} countries
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
              {editingCountry ? "Edit Country" : "Add Country"}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  ISO2 Code
                </label>
                <input
                  type="text"
                  value={formData.iso2}
                  onChange={(e) =>
                    setFormData({ ...formData, iso2: e.target.value })
                  }
                  maxLength={2}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 uppercase focus:border-blue-500 focus:outline-none"
                  placeholder="US"
                />
                {formErrors.iso2 && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.iso2}</p>
                )}
              </div>

              <div className="mb-6">
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Country Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                  placeholder="United States"
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
                  {editingCountry ? "Update" : "Create"}
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
              Delete Country
            </h3>
            <p className="mb-6 text-gray-600">
              Are you sure you want to delete{" "}
              <span className="font-semibold">{deleteConfirm.name}</span>? This
              action cannot be undone.
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
