"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle, ShieldCheck } from "lucide-react";
import { apiRequest } from "@/lib/api-client";
import { useCart } from "@/lib/cart-context";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, refreshCart, user } = useCart();
  const [shippingAddress, setShippingAddress] = useState(
    "100 Innovation Boulevard, Suite 400, San Francisco, CA 94105, USA"
  );
  const [paymentMethod, setPaymentMethod] = useState("simulated_card");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const items = cart?.items || [];
  const subtotal = Number(cart?.total_amount || 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shippingAddress.trim()) {
      setError("Please provide a valid shipping address");
      return;
    }

    setSubmitting(true);
    setError(null);

    const res = await apiRequest<any>("/orders/checkout", {
      method: "POST",
      body: JSON.stringify({
        shipping_address: shippingAddress,
        payment_method: paymentMethod,
      }),
    });

    setSubmitting(false);

    if (res.success && res.data) {
      await refreshCart();
      router.push(`/orders/${res.data.order_number}`);
    } else {
      setError(res.error?.message || res.message || "Failed to process simulated order.");
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <Link href="/cart" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition">
        <ArrowLeft className="h-4 w-4" /> Back to Cart
      </Link>

      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Simulated Checkout</h1>
        <p className="text-sm text-slate-500 mt-1">
          Complete your test order. Telemetry events will be dispatched to the monitoring log.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-50 border border-rose-200 p-4 text-sm text-rose-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-6">
          {/* Shipping Address */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900">1. Shipping Address</h2>
            <textarea
              rows={3}
              value={shippingAddress}
              onChange={(e) => setShippingAddress(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-3 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              required
            />
          </div>

          {/* Payment Method */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900">2. Payment Method</h2>
            <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-4 text-xs text-indigo-900 space-y-2">
              <div className="flex items-center gap-2 font-semibold">
                <ShieldCheck className="h-4 w-4 text-indigo-600" /> Simulated Payment Sandbox
              </div>
              <p>No actual credit cards or financial transactions are executed. This generates simulated payment telemetry.</p>
            </div>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="w-full rounded-lg border border-slate-300 p-2.5 text-sm text-slate-900 bg-white"
            >
              <option value="simulated_card">Simulated Visa / Mastercard (Instant Approval)</option>
              <option value="simulated_wire">Simulated Electronic Bank Wire</option>
            </select>
          </div>
        </div>

        {/* Summary */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4 h-fit">
          <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">Items Review</h2>
          <div className="space-y-2 text-xs">
            {items.map((it) => (
              <div key={it.id} className="flex justify-between text-slate-600">
                <span className="truncate max-w-[140px]">{it.product?.name} x{it.quantity}</span>
                <span className="font-semibold text-slate-900">${Number(it.subtotal).toFixed(2)}</span>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-200 pt-3 flex justify-between font-bold text-base text-slate-900">
            <span>Total</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>

          <button
            type="submit"
            disabled={submitting || items.length === 0}
            className="w-full rounded-lg bg-indigo-600 px-5 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            {submitting ? "Placing Order..." : "Place Simulated Order"}
          </button>
        </div>
      </form>
    </div>
  );
}
