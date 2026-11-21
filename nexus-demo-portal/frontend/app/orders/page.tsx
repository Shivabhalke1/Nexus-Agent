"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Package, ArrowRight, Clock } from "lucide-react";
import { apiRequest } from "@/lib/api-client";
import { useCart } from "@/lib/cart-context";

export default function OrdersPage() {
  const { user } = useCart();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchOrders() {
      setLoading(true);
      const res = await apiRequest<any>("/orders");
      if (res.success && res.data) {
        setOrders(res.data);
      }
      setLoading(false);
    }
    fetchOrders();
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="h-64 rounded-xl bg-slate-200 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Order History</h1>
        <p className="text-sm text-slate-500 mt-1">View previously placed simulated test orders and generated receipts</p>
      </div>

      {orders.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center space-y-4">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
            <Package className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">No Orders Found</h2>
          <p className="text-sm text-slate-500">You haven't completed any simulated shopping checkouts yet.</p>
          <Link
            href="/products"
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            Explore Catalog
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((ord) => (
            <div
              key={ord.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:border-slate-300 transition"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-bold text-slate-900">{ord.order_number}</span>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200 capitalize">
                    {ord.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {new Date(ord.created_at).toLocaleDateString()}
                  </span>
                  <span>&bull;</span>
                  <span>{ord.total_items} item(s)</span>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <span className="text-xs text-slate-500 block">Total Amount</span>
                  <span className="text-lg font-bold text-slate-900">${Number(ord.total_amount).toFixed(2)}</span>
                </div>
                <Link
                  href={`/orders/${ord.order_number}`}
                  className="rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition inline-flex items-center gap-1"
                >
                  View Details <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
