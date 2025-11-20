/**
 * Checkout page – Stripe PaymentIntent flow
 * 1) POST /api/payments/create to create a PaymentIntent (server-side)
 * 2) Confirm the intent in the browser via Stripe Elements
 * 3) Once Stripe reports success, call /api/esims/activate to provision the eSIM
 */

"use client";

import {
  Elements,
  LinkAuthenticationElement,
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import {
  Appearance,
  loadStripe,
  StripeElementsOptions,
} from "@stripe/stripe-js";
import { Button, Card } from "@tribi/ui";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, apiUrl } from "@/lib/apiConfig";

const fallbackStripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "pk_test_placeholder",
);

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

type PaymentStep = "review" | "collect" | "processing" | "success" | "error";

function useAuthToken() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setToken(localStorage.getItem("auth_token"));
  }, []);

  return token;
}

function OrderSummary({ order }: { order: Order | null }) {
  if (!order) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
        <div className="h-4 bg-gray-200 rounded w-1/3" />
      </div>
    );
  }

  return (
    <div className="bg-gray-50 p-6 rounded-lg mb-6">
      <h2 className="font-semibold text-gray-900 mb-4">Order Summary</h2>
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-600">Order ID</span>
          <span className="font-medium text-gray-900">#{order.id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Plan</span>
          <span className="font-medium text-gray-900">
            {order.plan_snapshot?.name || `Plan #${order.plan_id ?? "-"}`}
          </span>
        </div>
        {order.plan_snapshot?.country_name && (
          <div className="flex justify-between">
            <span className="text-gray-600">Destination</span>
            <span className="font-medium text-gray-900">
              {order.plan_snapshot.country_name}
              {order.plan_snapshot.country_iso2
                ? ` (${order.plan_snapshot.country_iso2.toUpperCase()})`
                : ""}
            </span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-600">Data & Duration</span>
          <span className="font-medium text-gray-900">
            {order.plan_snapshot?.data_gb
              ? `${order.plan_snapshot.data_gb} GB`
              : "—"}
            {order.plan_snapshot?.duration_days
              ? ` • ${order.plan_snapshot.duration_days} days`
              : ""}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Price</span>
          <span className="font-medium text-gray-900">
            {order.amount_major
              ? `${order.amount_major} ${order.currency}`
              : `${(order.amount_minor_units / 100).toFixed(2)} ${
                  order.currency
                }`}
          </span>
        </div>
        <div className="border-t border-gray-200 pt-3 flex justify-between">
          <span className="font-semibold text-gray-900">Total</span>
          <span className="font-bold text-lg text-indigo-600">
            {order.amount_major
              ? `${order.amount_major} ${order.currency}`
              : `${(order.amount_minor_units / 100).toFixed(2)} ${
                  order.currency
                }`}
          </span>
        </div>
      </div>
    </div>
  );
}

function StripeCheckout({
  onSuccess,
  onError,
}: {
  onSuccess: () => Promise<void> | void;
  onError: (message: string) => void;
}) {
  const stripe = useStripe();
  const elements = useElements();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!stripe || !elements) return;

      setIsSubmitting(true);
      setMessage(null);

      const result = await stripe.confirmPayment({
        elements,
        redirect: "if_required",
      });

      if (result.error) {
        const msg = result.error.message || "Payment failed. Please try again.";
        console.error("❌ Stripe confirmation error", result.error);
        setMessage(msg);
        onError(msg);
      } else {
        await onSuccess();
      }

      setIsSubmitting(false);
    },
    [stripe, elements, onSuccess, onError],
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <PaymentElement options={{ layout: "tabs" }} />
      <LinkAuthenticationElement
        options={{ defaultValues: { email: undefined } }}
      />
      {message && <p className="text-sm text-red-600">{message}</p>}
      <Button
        type="submit"
        disabled={!stripe || isSubmitting}
        className="w-full px-4 py-3 bg-indigo-600 text-white rounded"
      >
        {isSubmitting ? "Processing…" : "Pay securely"}
      </Button>
    </form>
  );
}

export default function CheckoutPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");
  const authToken = useAuthToken();

  const [order, setOrder] = useState<Order | null>(null);
  const [esim, setEsim] = useState<EsimProfile | null>(null);
  const [paymentStep, setPaymentStep] = useState<PaymentStep>("review");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [publishableKey, setPublishableKey] = useState<string | null>(null);

  const stripePromise = useMemo(() => {
    if (publishableKey) {
      return loadStripe(publishableKey);
    }
    return fallbackStripePromise;
  }, [publishableKey]);

  useEffect(() => {
    if (authToken === null) return; // still resolving
    if (!authToken) {
      router.push("/auth");
      return;
    }
    if (!orderId) {
      setError("Order ID missing");
      setPaymentStep("error");
      setLoading(false);
      return;
    }

    const numericOrderId = Number(orderId);
    if (Number.isNaN(numericOrderId)) {
      setError("Invalid order ID");
      setPaymentStep("error");
      setLoading(false);
      return;
    }

    const fetchOrder = async () => {
      try {
        setLoading(true);
        const response = await fetch(apiUrl("/api/orders/mine"), {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (!response.ok) {
          throw new Error("Failed to load order");
        }
        const orders: Order[] = await response.json();
        const found = orders.find((o) => o.id === numericOrderId);
        if (!found) {
          throw new Error("Order not found");
        }
        setOrder(found);
      } catch (err) {
        console.error("❌ Order fetch error", err);
        setError(err instanceof Error ? err.message : "Failed to load order");
        setPaymentStep("error");
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [authToken, orderId, router]);

  const handleProcessPayment = async () => {
    if (!order || !authToken) {
      router.push("/auth");
      return;
    }

    setPaymentStep("processing");
    setError("");

    try {
      const payment = await apiFetch<{
        intent_id: string;
        client_secret: string;
        publishable_key?: string;
        status: string;
        provider: string;
      }>("/api/payments/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ order_id: order.id, provider: "STRIPE" }),
      });

      if (!payment.client_secret) {
        throw new Error("Stripe client secret missing in response");
      }

      setClientSecret(payment.client_secret);
      if (payment.publishable_key) {
        setPublishableKey(payment.publishable_key);
      }
      setPaymentStep("collect");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Payment processing failed",
      );
      setPaymentStep("error");
    }
  };

  const activateEsim = useCallback(async () => {
    if (!order || !authToken) return;

    setPaymentStep("processing");

    try {
      const esimResponse = await apiFetch<EsimProfile>("/api/esims/activate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ order_id: order.id }),
      });

      setEsim(esimResponse);
      setOrder((prev) => (prev ? { ...prev, status: "paid" } : prev));
      setPaymentStep("success");
    } catch (err) {
      console.error("❌ eSIM activation failed", err);
      setError(err instanceof Error ? err.message : "Unable to activate eSIM");
      setPaymentStep("error");
    }
  }, [order, authToken]);

  if (loading && paymentStep === "review") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8">
          <p className="text-gray-600">Loading order...</p>
        </Card>
      </div>
    );
  }

  if (paymentStep === "error") {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-md mx-auto mt-8">
          <Card className="p-8 text-center">
            <div className="text-5xl mb-4">❌</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Payment Failed
            </h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button
              onClick={() => router.push("/account")}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded"
            >
              Back to Account
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  if (paymentStep === "processing") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="p-8 text-center space-y-4">
          <div className="text-5xl">💳</div>
          <h2 className="text-2xl font-semibold text-gray-900">
            Processing payment...
          </h2>
          <p className="text-gray-600">This may take just a few seconds.</p>
        </Card>
      </div>
    );
  }

  if (paymentStep === "success" && esim) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-md mx-auto mt-8">
          <Card className="p-8 text-center">
            <div className="text-5xl mb-4">✅</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Payment Successful!
            </h1>
            <p className="text-gray-600 mb-6">Your eSIM is ready to use</p>

            <div className="bg-blue-50 p-4 rounded mb-6 text-left">
              <p className="text-sm text-gray-600 mb-2">Activation Code:</p>
              <div className="flex items-center justify-between bg-white p-3 rounded border border-gray-200">
                <code className="font-mono text-sm text-gray-900">
                  {esim.activation_code || "Activation code not available yet"}
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
                Status:{" "}
                <span className="font-medium text-green-600">
                  {esim.status}
                </span>
              </p>
              {esim.iccid && (
                <p className="text-xs text-gray-500 mt-2">
                  ICCID:{" "}
                  <span className="font-mono text-gray-900">{esim.iccid}</span>
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
                Use this code or QR to install the profile on your device. Check
                the account page for full instructions.
              </p>
            </div>

            <Button
              onClick={() => router.push("/account")}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded"
            >
              View My Account
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  const appearance: Appearance = { theme: "stripe" };
  const elementsOptions: StripeElementsOptions | undefined = clientSecret
    ? { clientSecret, appearance }
    : undefined;

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto mt-8">
        <Card className="p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Complete Your Purchase
          </h1>
          <OrderSummary order={order} />

          {!clientSecret && (
            <>
              <p className="text-sm text-gray-600 mb-4">
                We use Stripe to process payments securely. Click below to start
                checkout.
              </p>
              <Button
                onClick={handleProcessPayment}
                disabled={loading || !order}
                className="w-full px-4 py-3 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-semibold"
              >
                Start Stripe Checkout
              </Button>
            </>
          )}

          {clientSecret && elementsOptions && (
            <div className="mt-6">
              <Elements stripe={stripePromise} options={elementsOptions}>
                <StripeCheckout
                  onSuccess={activateEsim}
                  onError={(msg) => setError(msg)}
                />
              </Elements>
            </div>
          )}

          <Button
            onClick={() => router.push("/account")}
            className="w-full px-4 py-2 bg-gray-200 text-gray-900 rounded hover:bg-gray-300 mt-4"
          >
            Cancel
          </Button>
          <p className="text-xs text-gray-500 text-center mt-4">
            Payments are processed securely by Stripe. Your card details never
            touch Tribi servers.
          </p>
        </Card>
      </div>
    </div>
  );
}
