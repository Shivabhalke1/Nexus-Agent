"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, ArrowLeft, Package, MapPin, CreditCard } from "lucide-react";
import { apiRequest } from "@/lib/api-client";

export default function OrderConfirmationPage() {
  const { orderNumber } = useParams();
  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchOrder() {
      setLoading(true);
      const res = await apiRequest<any>(`/orders/${orderNumber}`);
      if (res.success && res.data) {
        setOrder(res.data);
      }
      setLoading(false);
    }
    if (orderNumber) fetchOrder();
  }, [orderNumber]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="h-72 rounded-2xl bg-slate-200 animate-pulse" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8 text-center space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Order Not Found</h2>
        <Link href="/products" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600">
          <ArrowLeft className="h-4 w-4" /> Return to Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Banner */}
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-8 text-center space-y-3">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-600 text-white shadow-md">
          <CheckCircle2 className="h-8 w-8" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900">Order Confirmed!</h1>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          Thank you for testing the NEXUS Demo Portal. Your simulated checkout order has been recorded.
        </p>
        <div className="inline-block rounded-lg bg-white border border-emerald-200 px-4 py-1.5 font-mono text-sm font-bold text-slate-800">
          {order.order_number}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Items Table */}
        <div className="md:col-span-2 rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">Purchased Items</h2>
          <div className="divide-y divide-slate-100">
            {order.items?.map((it: any) => (
              <div key={it.id} className="py-3 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">{it.product?.name || `Product #${it.product_id}`}</h4>
                  <span className="text-xs text-slate-500">Qty: {it.quantity} &times; ${Number(it.unit_price).toFixed(2)}</span>
                </div>
                <div className="text-sm font-bold text-slate-900">
                  ${Number(it.subtotal).toFixed(2)}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-200 pt-4 flex justify-between font-bold text-base text-slate-900">
            <span>Total Paid (Simulated)</span>
            <span>${Number(order.total_amount).toFixed(2)}</span>
          </div>
        </div>

        {/* Shipping & Payment Meta */}
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-slate-400" /> Shipping Destination
            </h3>
            <p className="text-xs text-slate-700 leading-relaxed">{order.shipping_address}</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <CreditCard className="h-4 w-4 text-slate-400" /> Payment Sandbox
            </h3>
            <p className="text-xs text-slate-700 capitalize">{order.payment_method.replace("_", " ")}</p>
          </div>

          <Link
            href="/products"
            className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-center text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition inline-block"
          >
            Continue Browsing
          </Link>
        </div>
      </div>
    </div>
  );
}
