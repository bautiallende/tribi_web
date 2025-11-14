/**
 * Account page - User profile and orders
 * GET /api/auth/me to fetch user profile
 * GET /api/orders/mine to fetch user orders
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Button } from '@tribi/ui';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface User {
  id: number;
  email: string;
  name: string;
}

interface Order {
  id: number;
  plan_id: number;
  status: string;
  currency: string;
  amount_minor_units: number;
  created_at: string;
}

interface EsimProfile {
  id: number;
  order_id: number;
  activation_code: string;
  status: string;
}

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [esimData, setEsimData] = useState<Record<number, EsimProfile>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      router.push('/auth');
      return;
    }

    fetchUserProfile(token);
    fetchOrders(token);
  }, [router]);

  const fetchUserProfile = async (token: string) => {
    try {
      console.log('👤 Fetching user profile...');
      const response = await fetch(`${API_BASE}/api/auth/me`, {
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
    }
  };

  const fetchOrders = async (token: string) => {
    try {
      console.log('📦 Fetching orders...');
      const response = await fetch(`${API_BASE}/api/orders/mine`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log('📥 Orders response:', response.status);

      if (!response.ok) {
        throw new Error('Failed to fetch orders');
      }

      const data = await response.json();
      console.log('✅ Orders loaded:', data.length, 'orders');
      setOrders(data);

      // Fetch eSIM data for each paid order
      data.forEach(async (order: Order) => {
        if (order.status === 'paid') {
          try {
            const esimResponse = await fetch(`${API_BASE}/api/esims/activate`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({ order_id: order.id }),
            });

            if (esimResponse.ok) {
              const esim = await esimResponse.json();
              setEsimData((prev) => ({ ...prev, [order.id]: esim }));
            }
          } catch (err) {
            console.error('Error fetching eSIM:', err);
          }
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching orders');
    } finally {
      setLoading(false);
    }
  };

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
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Order ID</p>
                      <p className="text-lg font-medium text-gray-900">#{order.id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Status</p>
                      <p className={`text-lg font-medium ${
                        order.status === 'paid'
                          ? 'text-green-600'
                          : order.status === 'failed'
                          ? 'text-red-600'
                          : 'text-yellow-600'
                      }`}>
                        {order.status.toUpperCase()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Amount</p>
                      <p className="text-lg font-medium text-gray-900">
                        {(order.amount_minor_units / 100).toFixed(2)} {order.currency}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Date</p>
                      <p className="text-lg font-medium text-gray-900">
                        {new Date(order.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {/* eSIM Data */}
                  {esimData[order.id] && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h3 className="font-semibold text-gray-900 mb-2">eSIM Activation Code</h3>
                      <div className="flex items-center justify-between bg-gray-50 p-4 rounded">
                        <code className="font-mono text-sm text-gray-900 break-all">
                          {esimData[order.id].activation_code}
                        </code>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(esimData[order.id].activation_code);
                          }}
                          className="ml-4 px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                        >
                          Copy
                        </button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Status: <span className="font-medium">{esimData[order.id].status}</span>
                      </p>
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
