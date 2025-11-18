/**
 * Account page - User profile and orders
 * GET /api/auth/me to fetch user profile
 * GET /api/orders/mine to fetch user orders
 */

'use client';

import { apiUrl } from '@/lib/apiConfig';
import { Button, Card } from '@tribi/ui';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

interface User {
  id: number;
  email: string;
  name: string;
}

interface PlanSnapshot {
  id?: number;
  name?: string;
  description?: string;
  country_name?: string;
  country_iso2?: string;
  carrier_name?: string;
  data_gb?: number;
  duration_days?: number;
  price_minor_units?: number;
  currency?: string;
}

interface Order {
  id: number;
  plan_id?: number;
  status: string;
  currency: string;
  amount_minor_units: number;
  amount_major?: string;
  created_at: string;
  plan_snapshot?: PlanSnapshot | null;
}

interface EsimProfile {
  id: number;
  order_id: number | null;
  activation_code: string | null;
  iccid: string | null;
  status: string;
  created_at: string;
  qr_payload?: string | null;
  instructions?: string | null;
}

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [esims, setEsims] = useState<Record<number, EsimProfile>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUserProfile = useCallback(
    async (token: string) => {
      try {
        console.log('👤 Fetching user profile...');
        const response = await fetch(apiUrl('/api/auth/me'), {
          headers: { Authorization: `Bearer ${token}` },
        });

        console.log('📥 Profile response:', response.status);

        if (!response.ok) {
          throw new Error('Failed to fetch profile');
        }

        const data = await response.json();
        console.log('✅ User profile loaded:', data);
        setUser(data);
      } catch (err) {
        console.error('❌ Profile error:', err);
        setError(err instanceof Error ? err.message : 'Error fetching profile');
        router.push('/auth');
        throw err instanceof Error ? err : new Error('Failed to load profile');
      }
    },
    [router],
  );

  const fetchOrders = useCallback(async (token: string) => {
    try {
      console.log('📦 Fetching orders...');
      const response = await fetch(apiUrl('/api/orders/mine'), {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log('📥 Orders response:', response.status);

      if (!response.ok) {
        throw new Error('Failed to fetch orders');
      }

      const data = await response.json();
      console.log('✅ Orders loaded:', data.length, 'orders');
      setOrders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching orders');
      throw err instanceof Error ? err : new Error('Failed to load orders');
    }
  }, []);

  const fetchEsims = useCallback(async (token: string) => {
    try {
      console.log('📶 Fetching eSIMs...');
      const response = await fetch(apiUrl('/api/esims/mine'), {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log('📥 eSIM response:', response.status);

      if (!response.ok) {
        throw new Error('Failed to fetch eSIMs');
      }

      const data: EsimProfile[] = await response.json();
      console.log(`✅ eSIMs loaded: ${data.length} eSIMs`);
      const mapped = data.reduce<Record<number, EsimProfile>>((acc, esim) => {
        if (typeof esim.order_id === 'number') {
          acc[esim.order_id] = esim;
        }
        return acc;
      }, {});
      setEsims(mapped);
    } catch (err) {
      console.error('❌ eSIM error:', err);
      throw err instanceof Error ? err : new Error('Failed to fetch eSIMs');
    }
  }, []);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      router.push('/auth');
      return;
    }

    const loadAccount = async () => {
      try {
        setLoading(true);
        await Promise.all([
          fetchUserProfile(token),
          fetchOrders(token),
          fetchEsims(token),
        ]);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load account';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    loadAccount();
  }, [router, fetchUserProfile, fetchOrders, fetchEsims]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    router.push('/auth');
  };

  const handleNewPlan = () => {
    router.push('/plans/us'); // Example country code
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8">
          <p className="text-gray-600">Loading profile...</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Account</h1>
            <p className="text-gray-600 mt-1">{user?.email}</p>
          </div>
          <Button
            onClick={handleLogout}
            className="px-4 py-2 bg-gray-200 text-gray-900 rounded hover:bg-gray-300"
          >
            Logout
          </Button>
        </div>

        {error && (
          <Card className="mb-6 p-4 bg-red-50 border border-red-200">
            <p className="text-red-700">{error}</p>
          </Card>
        )}

        {/* Profile Card */}
        <Card className="mb-8 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="text-lg font-medium text-gray-900">{user?.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="text-lg font-medium text-gray-900">{user?.name || 'Not set'}</p>
            </div>
          </div>
        </Card>

        {/* Orders Section */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">My Orders</h2>
            <Button
              onClick={handleNewPlan}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Buy New Plan
            </Button>
          </div>

          {orders.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-gray-600 mb-4">No orders yet</p>
              <Button
                onClick={handleNewPlan}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                Get Started
              </Button>
            </Card>
          ) : (
            <div className="space-y-4">
              {orders.map((order) => (
                <Card key={order.id} className="p-6">
                  <div className="flex flex-col gap-4 mb-4">
                    <div className="flex flex-wrap justify-between gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Plan</p>
                        <p className="text-lg font-medium text-gray-900">
                          {order.plan_snapshot?.name || `Plan #${order.plan_id}`}
                        </p>
                        {order.plan_snapshot?.country_name && (
                          <p className="text-sm text-gray-500">
                            {order.plan_snapshot.country_name}
                            {order.plan_snapshot.country_iso2
                              ? ` (${order.plan_snapshot.country_iso2.toUpperCase()})`
                              : ''}
                          </p>
                        )}
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Status</p>
                        <p
                          className={`text-lg font-medium ${
                            order.status === 'paid'
                              ? 'text-green-600'
                              : order.status === 'failed'
                              ? 'text-red-600'
                              : 'text-yellow-600'
                          }`}
                        >
                          {order.status.toUpperCase()}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Amount</p>
                        <p className="text-lg font-medium text-gray-900">
                          {order.amount_major
                            ? `${order.amount_major} ${order.currency}`
                            : `${(order.amount_minor_units / 100).toFixed(2)} ${order.currency}`}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Date</p>
                        <p className="text-lg font-medium text-gray-900">
                          {new Date(order.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    {(order.plan_snapshot?.data_gb || order.plan_snapshot?.duration_days || order.plan_snapshot?.carrier_name) && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 border-t border-gray-100 pt-4">
                        {order.plan_snapshot?.data_gb && (
                          <div>
                            <p className="text-sm text-gray-500">Data</p>
                            <p className="text-base font-semibold text-gray-900">
                              {order.plan_snapshot.data_gb} GB
                            </p>
                          </div>
                        )}
                        {order.plan_snapshot?.duration_days && (
                          <div>
                            <p className="text-sm text-gray-500">Duration</p>
                            <p className="text-base font-semibold text-gray-900">
                              {order.plan_snapshot.duration_days} days
                            </p>
                          </div>
                        )}
                        {order.plan_snapshot?.carrier_name && (
                          <div>
                            <p className="text-sm text-gray-500">Carrier</p>
                            <p className="text-base font-semibold text-gray-900">
                              {order.plan_snapshot.carrier_name}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* eSIM Data */}
                  {esims[order.id] && (
                    <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-gray-900">eSIM Activation</h3>
                          <p className="text-xs text-gray-500">
                            Status: <span className="font-medium">{esims[order.id].status}</span>
                          </p>
                        </div>
                        {esims[order.id].activation_code && (
                          <div className="flex items-center gap-2">
                            <code className="font-mono text-sm text-gray-900 break-all">
                              {esims[order.id].activation_code}
                            </code>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(esims[order.id].activation_code ?? '');
                              }}
                              className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                            >
                              Copy
                            </button>
                          </div>
                        )}
                      </div>

                      {esims[order.id].iccid && (
                        <p className="text-sm text-gray-600">
                          ICCID: <span className="font-mono text-gray-900">{esims[order.id].iccid}</span>
                        </p>
                      )}

                      {esims[order.id].qr_payload && (
                        <div>
                          <p className="text-sm text-gray-600 mb-1">QR Payload</p>
                          <code className="block bg-gray-50 p-3 rounded text-xs text-gray-900">
                            {esims[order.id].qr_payload}
                          </code>
                        </div>
                      )}

                      {esims[order.id].instructions && (
                        <p className="text-sm text-gray-600">
                          {esims[order.id].instructions}
                        </p>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
