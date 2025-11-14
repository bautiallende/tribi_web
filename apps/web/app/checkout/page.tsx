/**
 * Checkout page - MOCK payment flow
 * POST /payments/create to create payment
 * POST /esims/activate to get activation code
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, Button } from '@tribi/ui';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface Order {
  id: number;
  plan_id: number;
  status: string;
  currency: string;
  amount_minor_units: number;
}

interface EsimProfile {
  id: number;
  activation_code: string;
  status: string;
}

export default function CheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get('order_id');

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

    if (!orderId) {
      setError('Order ID missing');
      setStep('error');
      setLoading(false);
      return;
    }

    // In a real app, we would fetch the order details
    // For now, we'll use the order_id passed via search params
    const mockOrder: Order = {
      id: parseInt(orderId),
      plan_id: 1,
      status: 'created',
      currency: 'USD',
      amount_minor_units: 1000,
    };

    setOrder(mockOrder);
    setLoading(false);
  }, [orderId, router]);

  const handleProcessPayment = async () => {
    if (!order) return;

    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      router.push('/auth');
      return;
    }

    setLoading(true);
    setStep('processing');

    try {
      // Create MOCK payment
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

      console.log('📥 Payment response:', paymentResponse.status);

      if (!paymentResponse.ok) {
        const errorData = await paymentResponse.json();
        throw new Error(errorData.detail || 'Payment failed');
      }

      // Activate eSIM
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

      const esimData = await esimResponse.json();
      setEsim(esimData);
      setOrder((prev) => prev ? { ...prev, status: 'paid' } : null);
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment processing failed');
      setStep('error');
    } finally {
      setLoading(false);
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
                <code className="font-mono text-sm text-gray-900">{esim.activation_code}</code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(esim.activation_code);
                  }}
                  className="ml-2 px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs hover:bg-indigo-200"
                >
                  Copy
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Status: <span className="font-medium text-green-600">{esim.status}</span>
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
                <span className="font-medium text-gray-900">1 GB / 30 Days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Price</span>
                <span className="font-medium text-gray-900">
                  {order ? `${(order.amount_minor_units / 100).toFixed(2)} ${order.currency}` : '-'}
                </span>
              </div>
              <div className="border-t border-gray-200 pt-3 flex justify-between">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="font-bold text-lg text-indigo-600">
                  {order ? `${(order.amount_minor_units / 100).toFixed(2)} ${order.currency}` : '-'}
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
              disabled={loading}
              className="w-full px-4 py-3 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-semibold disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Pay Now'}
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
