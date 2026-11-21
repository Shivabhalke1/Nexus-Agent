"use client";

import React from "react";
import Link from "next/link";
import { Trash2, ArrowRight, ShoppingBag, ArrowLeft } from "lucide-react";
import { useCart } from "@/lib/cart-context";

export default function CartPage() {
  const { cart, updateQuantity, removeFromCart, clearCart, isLoading } = useCart();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="h-64 rounded-xl bg-slate-200 animate-pulse" />
      </div>
    );
  }

  const items = cart?.items || [];
  const subtotal = Number(cart?.total_amount || 0);

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8 text-center space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
          <ShoppingBag className="h-8 w-8" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Your Cart is Empty</h2>
        <p className="text-sm text-slate-500">Add products from the catalog to test cart operations and checkout.</p>
        <Link
          href="/products"
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
        >
          <ArrowLeft className="h-4 w-4" /> Start Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Shopping Cart</h1>
        <button
          onClick={clearCart}
          className="text-xs font-semibold text-rose-600 hover:text-rose-500 transition"
        >
          Clear Cart
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Cart items list */}
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <img
                src={item.product?.image_url || "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80"}
                alt={item.product?.name || "Product"}
                className="h-20 w-20 rounded-lg object-cover bg-slate-100 flex-shrink-0"
              />

              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-slate-900 truncate">{item.product?.name}</h3>
                <span className="text-xs text-slate-500">Unit: ${Number(item.unit_price).toFixed(2)}</span>
              </div>

              {/* Quantity */}
              <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden bg-slate-50">
                <button
                  onClick={() => updateQuantity(item.id, item.quantity - 1)}
                  className="px-2.5 py-1 text-slate-600 hover:bg-slate-200 transition"
                >
                  -
                </button>
                <span className="px-3 text-xs font-semibold text-slate-900">{item.quantity}</span>
                <button
                  onClick={() => updateQuantity(item.id, item.quantity + 1)}
                  className="px-2.5 py-1 text-slate-600 hover:bg-slate-200 transition"
                >
                  +
                </button>
              </div>

              {/* Subtotal */}
              <div className="text-sm font-bold text-slate-900 w-20 text-right">
                ${Number(item.subtotal).toFixed(2)}
              </div>

              {/* Remove */}
              <button
                onClick={() => removeFromCart(item.id)}
                className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Order summary breakdown */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-6 h-fit">
          <h2 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-3">Order Summary</h2>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>Subtotal</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Simulated Express Shipping</span>
              <span className="text-emerald-600 font-medium">FREE</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Estimated Tax (0%)</span>
              <span>$0.00</span>
            </div>
            <div className="border-t border-slate-200 pt-3 flex justify-between font-bold text-base text-slate-900">
              <span>Total</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>
          </div>

          <Link
            href="/checkout"
            className="w-full rounded-lg bg-indigo-600 px-5 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition inline-flex items-center justify-center gap-2"
          >
            Proceed to Checkout <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
