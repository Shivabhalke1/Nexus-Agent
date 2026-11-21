"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ShoppingBag, Check, ShieldCheck, Truck, RefreshCw } from "lucide-react";
import { apiRequest } from "@/lib/api-client";
import { Product, useCart } from "@/lib/cart-context";

export default function ProductDetailPage() {
  const { slug } = useParams();
  const { addToCart } = useCart();
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    async function fetchProduct() {
      setLoading(true);
      const res = await apiRequest<Product>(`/products/${slug}`);
      if (res.success && res.data) {
        setProduct(res.data);
      }
      setLoading(false);
    }
    if (slug) fetchProduct();
  }, [slug]);

  const handleAddToCart = async () => {
    if (!product) return;
    setAdding(true);
    const success = await addToCart(product.id, quantity);
    setAdding(false);
    if (success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="h-96 rounded-2xl bg-slate-200 animate-pulse" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 text-center space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Product Not Found</h2>
        <p className="text-sm text-slate-500">The requested item could not be retrieved from the catalog.</p>
        <Link href="/products" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600">
          <ArrowLeft className="h-4 w-4" /> Back to Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <Link href="/products" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition">
        <ArrowLeft className="h-4 w-4" /> Back to Catalog
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
        {/* Image */}
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white aspect-square shadow-sm">
          <img
            src={product.image_url || "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80"}
            alt={product.name}
            className="h-full w-full object-cover object-center"
          />
        </div>

        {/* Details */}
        <div className="space-y-6">
          {product.category && (
            <span className="inline-block rounded-full bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-indigo-700">
              {product.category.name}
            </span>
          )}

          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">{product.name}</h1>
          <div className="text-2xl font-bold text-slate-900">${Number(product.price).toFixed(2)}</div>

          <p className="text-sm text-slate-600 leading-relaxed">{product.description}</p>

          <div className="border-t border-b border-slate-200 py-4 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">SKU: {product.sku}</span>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
              product.stock > 0 ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"
            }`}>
              {product.stock > 0 ? `In Stock (${product.stock} units)` : "Out of Stock"}
            </span>
          </div>

          {/* Add to Cart Actions */}
          <div className="flex items-center gap-4">
            <div className="flex items-center border border-slate-300 rounded-lg overflow-hidden bg-white">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="px-3 py-2 text-slate-600 hover:bg-slate-100 transition"
              >
                -
              </button>
              <span className="px-4 py-2 text-sm font-semibold text-slate-900">{quantity}</span>
              <button
                onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                className="px-3 py-2 text-slate-600 hover:bg-slate-100 transition"
              >
                +
              </button>
            </div>

            <button
              onClick={handleAddToCart}
              disabled={adding || product.stock === 0}
              className={`flex-1 rounded-lg px-6 py-3 text-sm font-semibold text-white shadow-sm transition inline-flex items-center justify-center gap-2 ${
                added ? "bg-emerald-600" : "bg-indigo-600 hover:bg-indigo-700"
              }`}
            >
              {added ? (
                <>
                  <Check className="h-4 w-4" /> Added to Cart
                </>
              ) : (
                <>
                  <ShoppingBag className="h-4 w-4" /> Add to Cart
                </>
              )}
            </button>
          </div>

          {/* Perks */}
          <div className="grid grid-cols-2 gap-3 pt-4 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-slate-400" /> Free simulated express shipping
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-slate-400" /> Non-destructive test sandbox
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
