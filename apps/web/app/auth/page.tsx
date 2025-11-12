/**
 * Auth page - OTP login flow
 * POST /auth/request-code to get OTP
 * POST /auth/verify to verify and get JWT
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Card } from '@tribi/ui';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function AuthPage() {
  const router = useRouter();
  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(`${API_BASE}/auth/request-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error requesting code');
      }

      setMessage(`OTP sent to ${email}. Check your email!`);
      setStep('otp');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error requesting OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(`${API_BASE}/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Invalid code');
      }

      const data = await response.json();
      const token = data.token;

      // Store JWT in httpOnly cookie via API call (server-side)
      // For now, store in localStorage as fallback
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', token);
      }

      setMessage('Login successful! Redirecting...');
      setTimeout(() => {
        router.push('/account');
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg">
        <div className="p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Tribi eSIM</h1>
          <p className="text-gray-600 mb-8">Sign in to your account</p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {message && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
              {message}
            </div>
          )}

          {step === 'email' ? (
            <form onSubmit={handleRequestCode} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <Button
                type="submit"
                disabled={loading || !email}
                className="w-full bg-indigo-600 hover:bg-indigo-700"
              >
                {loading ? 'Sending...' : 'Get OTP Code'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                OTP code sent to <strong>{email}</strong>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter 6-digit Code
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-center text-2xl font-mono tracking-widest focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-3">
                <Button
                  type="button"
                  onClick={() => {
                    setStep('email');
                    setCode('');
                    setMessage('');
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-900 rounded hover:bg-gray-300"
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  disabled={loading || code.length !== 6}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:opacity-50"
                >
                  {loading ? 'Verifying...' : 'Verify'}
                </Button>
              </div>
            </form>
          )}

          <p className="text-center text-xs text-gray-500 mt-6">
            Demo credentials: test@example.com (any code: 000000)
          </p>
        </div>
      </Card>
    </div>
  );
}
