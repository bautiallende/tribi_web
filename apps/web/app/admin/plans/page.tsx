'use client';

import { useState, useEffect, useRef } from 'react';
import { Button, SearchInput, Pagination, Dialog, Skeleton, useToast } from '@tribi/ui';

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
  name: string;
  country_id: number;
  carrier_id: number;
  data_gb: number;
  is_unlimited: boolean;
  duration_days: number;
  price_usd: number;
  description: string;
}

interface FormData {
  name: string;
  country_id: number | null;
  carrier_id: number | null;
  data_gb: number;
  is_unlimited: boolean;
  duration_days: number;
  price_usd: number;
  description: string;
}

export default function PlansPage() {
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Data state
  const [plans, setPlans] = useState<Plan[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [countryFilter, setCountryFilter] = useState<number | null>(null);
  const [carrierFilter, setCarrierFilter] = useState<number | null>(null);
  
  // Sorting state
  const [sortBy, setSortBy] = useState<'name' | 'price_usd' | 'duration_days' | 'data_gb'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 20;
  
  // Form state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [formData, setFormData] = useState<FormData>({
    name: '',
    country_id: null,
    carrier_id: null,
    data_gb: 0,
    is_unlimited: false,
    duration_days: 30,
    price_usd: 0,
    description: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  
  // Delete state
  const [deletingPlan, setDeletingPlan] = useState<Plan | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // CSV state
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  // Fetch countries and carriers for dropdowns
  useEffect(() => {
    fetchCountries();
    fetchCarriers();
  }, []);

  // Fetch plans when filters/search/sort/page changes
  useEffect(() => {
    fetchPlans();
  }, [searchQuery, countryFilter, carrierFilter, sortBy, sortOrder, currentPage]);

  const fetchCountries = async () => {
    try {
      const response = await fetch('/api/admin/countries?page_size=100', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setCountries(data.countries);
      }
    } catch (error) {
      console.error('Failed to fetch countries:', error);
    }
  };

  const fetchCarriers = async () => {
    try {
      const response = await fetch('/api/admin/carriers?page_size=100', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setCarriers(data.carriers);
      }
    } catch (error) {
      console.error('Failed to fetch carriers:', error);
    }
  };

  const fetchPlans = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      
      if (searchQuery) params.append('q', searchQuery);
      if (countryFilter) params.append('country_id', countryFilter.toString());
      if (carrierFilter) params.append('carrier_id', carrierFilter.toString());

      const response = await fetch(`/api/admin/plans?${params}`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data.plans);
        setTotalItems(data.total);
        setTotalPages(Math.ceil(data.total / pageSize));
      } else {
        showToast('Failed to fetch plans', 'error');
      }
    } catch (error) {
      showToast('Error fetching plans', 'error');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setCurrentPage(1);
  };

  const getSortIcon = (field: typeof sortBy) => {
    if (sortBy !== field) return '↕️';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  const handleFilterChange = (type: 'country' | 'carrier', value: string) => {
    const numValue = value ? parseInt(value, 10) : null;
    if (type === 'country') {
      setCountryFilter(numValue);
    } else {
      setCarrierFilter(numValue);
    }
    setCurrentPage(1);
  };

  const openCreateForm = () => {
    setFormData({
      name: '',
      country_id: null,
      carrier_id: null,
      data_gb: 0,
      is_unlimited: false,
      duration_days: 30,
      price_usd: 0,
      description: '',
    });
    setFormErrors({});
    setEditingPlan(null);
    setShowCreateForm(true);
  };

  const openEditForm = (plan: Plan) => {
    setFormData({
      name: plan.name,
      country_id: plan.country_id,
      carrier_id: plan.carrier_id,
      data_gb: plan.data_gb,
      is_unlimited: plan.is_unlimited,
      duration_days: plan.duration_days,
      price_usd: plan.price_usd,
      description: plan.description,
    });
    setFormErrors({});
    setEditingPlan(plan);
    setShowCreateForm(true);
  };

  const closeForm = () => {
    setShowCreateForm(false);
    setEditingPlan(null);
    setFormData({
      name: '',
      country_id: null,
      carrier_id: null,
      data_gb: 0,
      is_unlimited: false,
      duration_days: 30,
      price_usd: 0,
      description: '',
    });
    setFormErrors({});
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = 'Plan name is required';
    }

    if (!formData.country_id) {
      errors.country_id = 'Please select a country';
    }

    if (!formData.carrier_id) {
      errors.carrier_id = 'Please select a carrier';
    }

    if (formData.data_gb < 0) {
      errors.data_gb = 'Data must be 0 or positive (0 = unlimited)';
    }

    if (formData.duration_days <= 0) {
      errors.duration_days = 'Duration must be positive';
    }

    if (formData.price_usd <= 0) {
      errors.price_usd = 'Price must be positive';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      showToast('Please fix form errors', 'error');
      return;
    }

    try {
      const url = editingPlan
        ? `/api/admin/plans/${editingPlan.id}`
        : '/api/admin/plans';
      const method = editingPlan ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        showToast(
          editingPlan ? 'Plan updated successfully' : 'Plan created successfully',
          'success'
        );
        closeForm();
        fetchPlans();
      } else {
        const error = await response.json();
        showToast(error.detail || 'Operation failed', 'error');
      }
    } catch (error) {
      showToast('Error submitting form', 'error');
      console.error('Error:', error);
    }
  };

  const handleDelete = async () => {
    if (!deletingPlan) return;

    setIsDeleting(true);
    try {
      const response = await fetch(`/api/admin/plans/${deletingPlan.id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        showToast('Plan deleted successfully', 'success');
        setDeletingPlan(null);
        fetchPlans();
      } else {
        showToast('Failed to delete plan', 'error');
      }
    } catch (error) {
      showToast('Error deleting plan', 'error');
      console.error('Error:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await fetch('/api/admin/plans/export', {
        credentials: 'include',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'plans_export.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showToast('Plans exported successfully', 'success');
      } else {
        showToast('Failed to export plans', 'error');
      }
    } catch (error) {
      showToast('Error exporting plans', 'error');
      console.error('Error:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/admin/plans/import', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        showToast(
          `Import successful: ${result.created} created, ${result.updated} updated`,
          'success'
        );
        fetchPlans();
      } else {
        showToast(
          `Import failed: ${result.errors?.length || 0} errors`,
          'error'
        );
        console.error('Import errors:', result.errors);
      }
    } catch (error) {
      showToast('Error importing plans', 'error');
      console.error('Error:', error);
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const getCountryName = (countryId: number) => {
    return countries.find((c) => c.id === countryId)?.name || `Country ${countryId}`;
  };

  const getCarrierName = (carrierId: number) => {
    return carriers.find((c) => c.id === carrierId)?.name || `Carrier ${carrierId}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold dark:text-white">Plans Management</h1>
        <div className="flex gap-2">
          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting ? 'Exporting...' : '📥 Export CSV'}
          </Button>
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={isImporting}
          >
            {isImporting ? 'Importing...' : '📤 Import CSV'}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleImport}
            style={{ display: 'none' }}
          />
          <Button onClick={openCreateForm}>Create Plan</Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <SearchInput
            onSearch={handleSearch}
            placeholder="Search plans by name..."
            debounceMs={300}
          />
        </div>
        <select
          value={countryFilter || ''}
          onChange={(e) => handleFilterChange('country', e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
        >
          <option value="">All Countries</option>
          {countries.map((country) => (
            <option key={country.id} value={country.id}>
              {country.name}
            </option>
          ))}
        </select>
        <select
          value={carrierFilter || ''}
          onChange={(e) => handleFilterChange('carrier', e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                ID
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => handleSort('name')}
              >
                Name {getSortIcon('name')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Country
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Carrier
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => handleSort('data_gb')}
              >
                Data (GB) {getSortIcon('data_gb')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => handleSort('duration_days')}
              >
                Duration {getSortIcon('duration_days')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => handleSort('price_usd')}
              >
                Price (USD) {getSortIcon('price_usd')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-8" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-32" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-24" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-24" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-16" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-16" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-16" /></td>
                  <td className="px-6 py-4"><Skeleton className="h-4 w-24" /></td>
                </tr>
              ))
            ) : plans.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  {searchQuery || countryFilter || carrierFilter
                    ? 'No plans found matching your filters'
                    : 'No plans yet. Create one to get started!'}
                </td>
              </tr>
            ) : (
              plans.map((plan) => (
                <tr key={plan.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {plan.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {plan.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                    {getCountryName(plan.country_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                    {getCarrierName(plan.carrier_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                    {plan.is_unlimited ? 'Unlimited' : plan.data_gb}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                    {plan.duration_days} days
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                    ${plan.price_usd.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => openEditForm(plan)}
                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeletingPlan(plan)}
                      className="text-red-600 hover:text-red-800 dark:text-red-400"
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
      {!loading && totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          totalItems={totalItems}
          itemsPerPage={pageSize}
        />
      )}

      {/* Create/Edit Form Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4 dark:text-white">
              {editingPlan ? 'Edit Plan' : 'Create Plan'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Plan Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                {formErrors.name && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.name}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Country *
                  </label>
                  <select
                    value={formData.country_id || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, country_id: parseInt(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Select country</option>
                    {countries.map((country) => (
                      <option key={country.id} value={country.id}>
                        {country.name}
                      </option>
                    ))}
                  </select>
                  {formErrors.country_id && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.country_id}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Carrier *
                  </label>
                  <select
                    value={formData.carrier_id || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, carrier_id: parseInt(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="">Select carrier</option>
                    {carriers.map((carrier) => (
                      <option key={carrier.id} value={carrier.id}>
                        {carrier.name}
                      </option>
                    ))}
                  </select>
                  {formErrors.carrier_id && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.carrier_id}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data (GB) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.data_gb}
                    onChange={(e) =>
                      setFormData({ ...formData, data_gb: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  {formErrors.data_gb && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.data_gb}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">Use 0 for unlimited plans</p>
                </div>

                <div>
                  <label className="flex items-center space-x-2 mt-6">
                    <input
                      type="checkbox"
                      checked={formData.is_unlimited}
                      onChange={(e) =>
                        setFormData({ ...formData, is_unlimited: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Unlimited Plan
                    </span>
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Duration (days) *
                  </label>
                  <input
                    type="number"
                    value={formData.duration_days}
                    onChange={(e) =>
                      setFormData({ ...formData, duration_days: parseInt(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  {formErrors.duration_days && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.duration_days}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Price (USD) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_usd}
                    onChange={(e) =>
                      setFormData({ ...formData, price_usd: parseFloat(e.target.value) })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  {formErrors.price_usd && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.price_usd}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" onClick={closeForm} variant="secondary">
                  Cancel
                </Button>
                <Button type="submit">
                  {editingPlan ? 'Update Plan' : 'Create Plan'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        isOpen={!!deletingPlan}
        onClose={() => setDeletingPlan(null)}
        onConfirm={handleDelete}
        title="Delete Plan"
        message={`Are you sure you want to delete "${deletingPlan?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
