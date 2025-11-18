/**
 * Checkout page - MOCK payment flow
 * POST /payments/create to create payment
 * POST /esims/activate to get activation code
 */

'use client';

import { Button, Card } from '@tribi/ui';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

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
  plan_snapshot?: PlanSnapshot | null;
}

interface EsimProfile {
  id: number;
  order_id?: number | null;
  activation_code: string | null;
  iccid: string | null;
  status: string;
  qr_payload?: string | null;
  instructions?: string | null;
}

export default function CheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order_id');

  const [authToken, setAuthToken] = useState<string | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [esim, setEsim] = useState<EsimProfile | null>(null);
  const [step, setStep] = useState<'review' | 'processing' | 'success' | 'error'>('review');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      router.push('/auth');
      return;
    }

    setAuthToken(token);

    if (!orderId) {
      setError('Order ID missing');
      setStep('error');
      setLoading(false);
      return;
    }

    const numericOrderId = Number(orderId);
    if (Number.isNaN(numericOrderId)) {
      setError('Invalid order ID');
      setStep('error');
      setLoading(false);
      return;
    }

    const fetchOrder = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE}/api/orders/mine`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          throw new Error('Failed to load order');
        }

        const orders: Order[] = await response.json();
        const found = orders.find((o) => o.id === numericOrderId);

        if (!found) {
          throw new Error('Order not found');
        }

        setOrder(found);
      } catch (err) {
        console.error('❌ Order fetch error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load order');
        setStep('error');
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [orderId, router]);

  const handleProcessPayment = async () => {
    if (!order) return;

    const token = authToken || (typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null);
    if (!token) {
      router.push('/auth');
      return;
    }

    setStep('processing');
    setError('');

    try {
      console.log('💳 Creating payment...');
      const paymentResponse = await fetch(`${API_BASE}/api/payments/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          order_id: order.id,
          provider: 'MOCK',
        }),
      });

      if (!paymentResponse.ok) {
        const errorData = await paymentResponse.json();
        throw new Error(errorData.detail || 'Payment failed');
      }

      console.log('📱 Activating eSIM...');
      const esimResponse = await fetch(`${API_BASE}/api/esims/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ order_id: order.id }),
      });

      if (!esimResponse.ok) {
        const errorData = await esimResponse.json();
        throw new Error(errorData.detail || 'eSIM activation failed');
      }

      const esimData: EsimProfile = await esimResponse.json();
      setEsim(esimData);
      setOrder((prev) => (prev ? { ...prev, status: 'paid' } : prev));
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment processing failed');
      setStep('error');
    }
  };

  if (loading && step === 'review') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8">
          <p className="text-gray-600">Loading order...</p>
        </Card>
      </div>
    );
  }

  if (step === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-md mx-auto mt-8">
          <Card className="p-8 text-center">
            <div className="text-5xl mb-4">❌</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Payment Failed</h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex flex-col gap-3">
              <Button
                onClick={() => router.push('/account')}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                Back to Account
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  if (step === 'processing') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="p-8 text-center space-y-4">
          <div className="text-5xl">💳</div>
          <h2 className="text-2xl font-semibold text-gray-900">Processing payment...</h2>
          <p className="text-gray-600">This may take just a few seconds.</p>
        </Card>
      </div>
    );
  }

  if (step === 'success' && esim) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-md mx-auto mt-8">
          <Card className="p-8 text-center">
            <div className="text-5xl mb-4">✅</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
            <p className="text-gray-600 mb-6">Your eSIM is ready to use</p>

            <div className="bg-blue-50 p-4 rounded mb-6 text-left">
              <p className="text-sm text-gray-600 mb-2">Activation Code:</p>
              <div className="flex items-center justify-between bg-white p-3 rounded border border-gray-200">
                <code className="font-mono text-sm text-gray-900">
                  {esim.activation_code || 'Activation code not available yet'}
                </code>
                <button
                  onClick={() => {
                    if (esim.activation_code) {
                      navigator.clipboard.writeText(esim.activation_code);
                    }
                  }}
                  disabled={!esim.activation_code}
                  className="ml-2 px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs hover:bg-indigo-200 disabled:opacity-50"
                >
                  Copy
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Status: <span className="font-medium text-green-600">{esim.status}</span>
              </p>
              {esim.iccid && (
                <p className="text-xs text-gray-500 mt-2">
                  ICCID: <span className="font-mono text-gray-900">{esim.iccid}</span>
                </p>
              )}
              {esim.qr_payload && (
                <div className="mt-4">
                  <p className="text-sm text-gray-600 mb-1">QR Payload</p>
                  <code className="block bg-white p-3 rounded border border-dashed border-indigo-200 text-xs text-gray-900">
                    {esim.qr_payload}
                  </code>
                </div>
              )}
              <p className="text-sm text-gray-600 mt-4">
                {esim.instructions ||
                  'Install via Settings > Cellular > Add eSIM and scan the QR or enter the activation code manually.'}
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <Button
                onClick={() => router.push('/account')}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                View My Account
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto mt-8">
        <Card className="p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Complete Your Purchase</h1>

          {/* Order Summary */}
          <div className="bg-gray-50 p-6 rounded-lg mb-6">
            <h2 className="font-semibold text-gray-900 mb-4">Order Summary</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Order ID</span>
                <span className="font-medium text-gray-900">#{order?.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Plan</span>
                <span className="font-medium text-gray-900">
                  {order?.plan_snapshot?.name || `Plan #${order?.plan_id ?? '-'}`}
                </span>
              </div>
              {order?.plan_snapshot?.country_name && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Destination</span>
                  <span className="font-medium text-gray-900">
                    {order.plan_snapshot.country_name}
                    {order.plan_snapshot.country_iso2
                      ? ` (${order.plan_snapshot.country_iso2.toUpperCase()})`
                      : ''}
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Data & Duration</span>
                <span className="font-medium text-gray-900">
                  {order?.plan_snapshot?.data_gb ? `${order.plan_snapshot.data_gb} GB` : '—'}
                  {order?.plan_snapshot?.duration_days ? ` • ${order.plan_snapshot.duration_days} days` : ''}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Price</span>
                <span className="font-medium text-gray-900">
                  {order
                    ? order.amount_major
                      ? `${order.amount_major} ${order.currency}`
                      : `${(order.amount_minor_units / 100).toFixed(2)} ${order.currency}`
                    : '-'}
                </span>
              </div>
              <div className="border-t border-gray-200 pt-3 flex justify-between">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="font-bold text-lg text-indigo-600">
                  {order
                    ? order.amount_major
                      ? `${order.amount_major} ${order.currency}`
                      : `${(order.amount_minor_units / 100).toFixed(2)} ${order.currency}`
                    : '-'}
                </span>
              </div>
            </div>
          </div>

          {/* Payment Method */}
          <div className="mb-6">
            <h2 className="font-semibold text-gray-900 mb-4">Payment Method</h2>
            <div className="border-2 border-indigo-500 rounded-lg p-4 bg-indigo-50">
              <p className="font-medium text-gray-900">💳 Mock Payment</p>
              <p className="text-sm text-gray-600">Test payment processor</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-3">
            <Button
              onClick={handleProcessPayment}
              disabled={loading || !order}
              className="w-full px-4 py-3 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-semibold disabled:opacity-50"
            >
              {loading || !order ? 'Loading...' : 'Pay Now'}
            </Button>
            <Button
              onClick={() => router.push('/account')}
              disabled={loading}
              className="w-full px-4 py-2 bg-gray-200 text-gray-900 rounded hover:bg-gray-300"
            >
              Cancel
            </Button>
          </div>

          <p className="text-xs text-gray-500 text-center mt-4">
            This is a demo payment. No real charges will be made.
          </p>
        </Card>
      </div>
    </div>
  );
}
