"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ShoppingBag, Check } from "lucide-react";
import { Product, useCart } from "@/lib/cart-context";

export default function ProductCard({ product }: { product: Product }) {
  const { addToCart } = useCart();
  const [added, setAdded] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    setLoading(true);
    const success = await addToCart(product.id, 1);
    setLoading(false);
    if (success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 1500);
    }
  };

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white transition hover:shadow-lg hover:border-slate-300">
      {/* Product Image */}
      <Link href={`/products/${product.slug}`} className="relative aspect-square w-full overflow-hidden bg-slate-100">
        <img
          src={product.image_url || "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80"}
          alt={product.name}
          className="h-full w-full object-cover object-center transition duration-300 group-hover:scale-105"
        />
        {product.stock <= 5 && product.stock > 0 && (
          <span className="absolute top-2 left-2 rounded-full bg-amber-500/90 backdrop-blur px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
            Only {product.stock} left
          </span>
        )}
      </Link>

      {/* Info Container */}
      <div className="flex flex-1 flex-col p-4">
        {product.category && (
          <span className="text-[11px] font-semibold uppercase tracking-wider text-indigo-600 mb-1">
            {product.category.name}
          </span>
        )}
        <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600 transition line-clamp-1">
          <Link href={`/products/${product.slug}`}>{product.name}</Link>
        </h3>
        <p className="mt-1 text-xs text-slate-500 line-clamp-2 flex-1">
          {product.description}
        </p>

        {/* Price & Add to Cart button */}
        <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
          <div className="text-lg font-bold text-slate-900">
            ${Number(product.price).toFixed(2)}
          </div>
          <button
            onClick={handleAdd}
            disabled={loading || product.stock === 0}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm transition ${
              added
                ? "bg-emerald-600 text-white"
                : "bg-indigo-600 text-white hover:bg-indigo-700"
            }`}
          >
            {added ? (
              <>
                <Check className="h-3.5 w-3.5" />
                Added
              </>
            ) : (
              <>
                <ShoppingBag className="h-3.5 w-3.5" />
                Add
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
