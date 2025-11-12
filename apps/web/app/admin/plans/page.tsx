"use client";

import { useState, useEffect } from "react";

interface Country {
  id: number;
  iso2: string;
  name: string;
}

interface Carrier {
  id: number;
  name: string;
}

interface Plan {
  id: number;
  country_id: number;
  carrier_id: number;
  name: string;
  data_gb: number;
  duration_days: number;
  price_usd: number;
  description?: string;
  is_unlimited: boolean;
}

interface PaginatedResponse {
  items: Plan[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function PlansAdmin() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [carrierFilter, setCarrierFilter] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Plan | null>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    country_id: "",
    carrier_id: "",
    name: "",
    data_gb: "",
    duration_days: "",
    price_usd: "",
    description: "",
    is_unlimited: false,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const pageSize = 20;

  // Fetch countries and carriers on mount
  useEffect(() => {
    fetchCountries();
    fetchCarriers();
  }, []);

  // Fetch plans when filters change
  useEffect(() => {
    fetchPlans();
  }, [page, search, countryFilter, carrierFilter]);

  const fetchCountries = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/countries", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setCountries(data);
      }
    } catch (error) {
      console.error("Failed to fetch countries:", error);
    }
  };

  const fetchCarriers = async () => {
    try {
      const response = await fetch("http://localhost:8000/admin/carriers?page=1&page_size=1000", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setCarriers(data.items);
      }
    } catch (error) {
      console.error("Failed to fetch carriers:", error);
    }
  };

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...(search && { q: search }),
        ...(countryFilter && { country_id: countryFilter }),
        ...(carrierFilter && { carrier_id: carrierFilter }),
      });

      const response = await fetch(
        `http://localhost:8000/admin/plans?${params}`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) throw new Error("Failed to fetch plans");

      const data: PaginatedResponse = await response.json();
      setPlans(data.items);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (error) {
      showToast("Failed to load plans", "error");
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.country_id) errors.country_id = "Country is required";
    if (!formData.carrier_id) errors.carrier_id = "Carrier is required";
    if (!formData.name.trim()) errors.name = "Plan name is required";
    
    const dataGb = parseFloat(formData.data_gb);
    if (!formData.data_gb || isNaN(dataGb) || dataGb < 0) {
      errors.data_gb = "Data must be a non-negative number";
    }

    const duration = parseInt(formData.duration_days);
    if (!formData.duration_days || isNaN(duration) || duration <= 0) {
      errors.duration_days = "Duration must be a positive number";
    }

    const price = parseFloat(formData.price_usd);
    if (!formData.price_usd || isNaN(price) || price < 0) {
      errors.price_usd = "Price must be a non-negative number";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreate = () => {
    setEditingPlan(null);
    setFormData({
      country_id: "",
      carrier_id: "",
      name: "",
      data_gb: "",
      duration_days: "",
      price_usd: "",
      description: "",
      is_unlimited: false,
    });
    setFormErrors({});
    setShowModal(true);
  };

  const handleEdit = (plan: Plan) => {
    setEditingPlan(plan);
    setFormData({
      country_id: plan.country_id.toString(),
      carrier_id: plan.carrier_id.toString(),
      name: plan.name,
      data_gb: plan.data_gb.toString(),
      duration_days: plan.duration_days.toString(),
      price_usd: plan.price_usd.toString(),
      description: plan.description || "",
      is_unlimited: plan.is_unlimited,
    });
    setFormErrors({});
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      const url = editingPlan
        ? `http://localhost:8000/admin/plans/${editingPlan.id}`
        : "http://localhost:8000/admin/plans";

      const method = editingPlan ? "PUT" : "POST";

      const payload = {
        country_id: parseInt(formData.country_id),
        carrier_id: parseInt(formData.carrier_id),
        name: formData.name,
        data_gb: parseFloat(formData.data_gb),
        duration_days: parseInt(formData.duration_days),
        price_usd: parseFloat(formData.price_usd),
        description: formData.description || null,
        is_unlimited: formData.is_unlimited,
      };

      // Optimistic update
      if (editingPlan) {
        setPlans((prev) =>
          prev.map((p) =>
            p.id === editingPlan.id ? { ...p, ...payload } : p
          )
        );
      }

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save plan");
      }

      const savedPlan: Plan = await response.json();

      if (editingPlan) {
        setPlans((prev) =>
          prev.map((p) => (p.id === savedPlan.id ? savedPlan : p))
        );
      } else {
        fetchPlans();
      }

      showToast(editingPlan ? "Plan updated" : "Plan created", "success");
      setShowModal(false);
    } catch (error: any) {
      showToast(error.message, "error");
      if (editingPlan) {
        fetchPlans();
      }
    }
  };

  const handleDelete = async (plan: Plan) => {
    try {
      // Optimistic delete
      setPlans((prev) => prev.filter((p) => p.id !== plan.id));
      setDeleteConfirm(null);

      const response = await fetch(
        `http://localhost:8000/admin/plans/${plan.id}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete plan");
      }

      showToast("Plan deleted", "success");
      fetchPlans();
    } catch (error: any) {
      showToast(error.message, "error");
      fetchPlans();
    }
  };

  const getCountryName = (countryId: number) => {
    return countries.find((c) => c.id === countryId)?.name || `ID ${countryId}`;
  };

  const getCarrierName = (carrierId: number) => {
    return carriers.find((c) => c.id === carrierId)?.name || `ID ${carrierId}`;
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Plans</h2>
        <button
          onClick={handleCreate}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          + Add Plan
        </button>
      </div>

      {/* Filters */}
      <div className="mb-4 grid gap-4 md:grid-cols-3">
        <input
          type="text"
          placeholder="Search by name..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
        />
        <select
          value={countryFilter}
          onChange={(e) => {
            setCountryFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
        >
          <option value="">All Countries</option>
          {countries.map((country) => (
            <option key={country.id} value={country.id}>
              {country.name}
            </option>
          ))}
        </select>
        <select
          value={carrierFilter}
          onChange={(e) => {
            setCarrierFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
        >
          <option value="">All Carriers</option>
          {carriers.map((carrier) => (
            <option key={carrier.id} value={carrier.id}>
              {carrier.name}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Country
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Carrier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Data
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Price
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : plans.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    No plans found
                  </td>
                </tr>
              ) : (
                plans.map((plan) => (
                  <tr key={plan.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                      {plan.name}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-700">
                      {getCountryName(plan.country_id)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-700">
                      {getCarrierName(plan.carrier_id)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-700">
                      {plan.is_unlimited ? "Unlimited" : `${plan.data_gb} GB`}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-700">
                      {plan.duration_days} days
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-700">
                      ${plan.price_usd.toFixed(2)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                      <button
                        onClick={() => handleEdit(plan)}
                        className="mr-3 text-blue-600 hover:text-blue-800"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => setDeleteConfirm(plan)}
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
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {plans.length} of {total} plans
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-xl font-bold text-gray-900">
              {editingPlan ? "Edit Plan" : "Add Plan"}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Country *
                  </label>
                  <select
                    value={formData.country_id}
                    onChange={(e) =>
                      setFormData({ ...formData, country_id: e.target.value })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Select country</option>
                    {countries.map((country) => (
                      <option key={country.id} value={country.id}>
                        {country.name}
                      </option>
                    ))}
                  </select>
                  {formErrors.country_id && (
                    <p className="mt-1 text-sm text-red-600">
                      {formErrors.country_id}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Carrier *
                  </label>
                  <select
                    value={formData.carrier_id}
                    onChange={(e) =>
                      setFormData({ ...formData, carrier_id: e.target.value })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Select carrier</option>
                    {carriers.map((carrier) => (
                      <option key={carrier.id} value={carrier.id}>
                        {carrier.name}
                      </option>
                    ))}
                  </select>
                  {formErrors.carrier_id && (
                    <p className="mt-1 text-sm text-red-600">
                      {formErrors.carrier_id}
                    </p>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Plan Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                    placeholder="USA 10GB"
                  />
                  {formErrors.name && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Data (GB) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.data_gb}
                    onChange={(e) =>
                      setFormData({ ...formData, data_gb: e.target.value })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                    placeholder="10.0"
                  />
                  {formErrors.data_gb && (
                    <p className="mt-1 text-sm text-red-600">
                      {formErrors.data_gb}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Duration (days) *
                  </label>
                  <input
                    type="number"
                    value={formData.duration_days}
                    onChange={(e) =>
                      setFormData({ ...formData, duration_days: e.target.value })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                    placeholder="30"
                  />
                  {formErrors.duration_days && (
                    <p className="mt-1 text-sm text-red-600">
                      {formErrors.duration_days}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Price (USD) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_usd}
                    onChange={(e) =>
                      setFormData({ ...formData, price_usd: e.target.value })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                    placeholder="25.50"
                  />
                  {formErrors.price_usd && (
                    <p className="mt-1 text-sm text-red-600">
                      {formErrors.price_usd}
                    </p>
                  )}
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_unlimited}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          is_unlimited: e.target.checked,
                        })
                      }
                      className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Unlimited Data
                    </span>
                  </label>
                </div>

                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Description (optional)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                    placeholder="Best plan for travelers..."
                  />
                </div>
              </div>

              <div className="mt-6 flex gap-3">
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
                  {editingPlan ? "Update" : "Create"}
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
            <h3 className="mb-4 text-xl font-bold text-gray-900">Delete Plan</h3>
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
