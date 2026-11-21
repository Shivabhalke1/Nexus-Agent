"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ShieldAlert, Cpu, Activity, Zap, CheckCircle } from "lucide-react";
import { apiRequest } from "@/lib/api-client";
import { Product } from "@/lib/cart-context";
import ProductCard from "@/components/ProductCard";

export default function HomePage() {
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const [prodRes, catRes] = await Promise.all([
        apiRequest<any>("/products?page=1&page_size=4"),
        apiRequest<any>("/products/categories"),
      ]);

      if (prodRes.success && prodRes.data) {
        setFeaturedProducts(prodRes.data.items || []);
      }
      if (catRes.success && catRes.data) {
        setCategories(catRes.data || []);
      }
      setLoading(false);
    }
    loadData();
  }, []);

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-indigo-800 to-slate-950 text-white py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-indigo-300 bg-indigo-950/60 border border-indigo-700/50 rounded-full">
                CICADA 2026 Observability Testbed
              </div>
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight leading-tight">
                Next-Generation E-Commerce with Deep System Telemetry
              </h1>
              <p className="text-lg text-indigo-200">
                Simulating realistic online shopping journeys, transaction workloads, and 6 controlled failure scenarios for the NEXUS OBSERVE platform.
              </p>
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  href="/products"
                  className="rounded-lg bg-indigo-500 px-5 py-3 text-sm font-semibold text-white shadow-lg hover:bg-indigo-400 transition inline-flex items-center gap-2"
                >
                  Explore Products
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/simulator"
                  className="rounded-lg border border-amber-400/40 bg-amber-500/10 px-5 py-3 text-sm font-semibold text-amber-300 hover:bg-amber-500/20 transition inline-flex items-center gap-2"
                >
                  <ShieldAlert className="h-4 w-4" />
                  Controlled Failure Simulator
                </Link>
              </div>
            </div>

            {/* Architecture Card */}
            <div className="rounded-2xl border border-indigo-700/40 bg-indigo-950/40 p-6 shadow-2xl backdrop-blur">
              <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-400 mb-4 flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Real-Time Testbed Telemetry
              </h3>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="rounded-lg bg-indigo-900/40 p-3 border border-indigo-800/40">
                  <span className="text-indigo-300 block">HTTP Request Tracing</span>
                  <span className="font-semibold text-white text-sm">X-Request-ID Header</span>
                </div>
                <div className="rounded-lg bg-indigo-900/40 p-3 border border-indigo-800/40">
                  <span className="text-indigo-300 block">Diagnostics Check</span>
                  <span className="font-semibold text-emerald-400 text-sm">/api/v1/health</span>
                </div>
                <div className="rounded-lg bg-indigo-900/40 p-3 border border-indigo-800/40">
                  <span className="text-indigo-300 block">Failure Scenarios</span>
                  <span className="font-semibold text-amber-300 text-sm">6 Safety Modes</span>
                </div>
                <div className="rounded-lg bg-indigo-900/40 p-3 border border-indigo-800/40">
                  <span className="text-indigo-300 block">Audit Event Log</span>
                  <span className="font-semibold text-white text-sm">Structured JSON</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Preview */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">Featured Categories</h2>
            <p className="text-sm text-slate-500">Explore our curated collections of consumer electronics</p>
          </div>
          <Link href="/products" className="text-sm font-semibold text-indigo-600 hover:text-indigo-500">
            View All &rarr;
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              href={`/products?category=${cat.slug}`}
              className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition"
            >
              <h3 className="text-base font-semibold text-slate-900 group-hover:text-indigo-600 transition">
                {cat.name}
              </h3>
              <p className="mt-1 text-xs text-slate-500 line-clamp-2">{cat.description}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured Products */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">Featured Products</h2>
            <p className="text-sm text-slate-500">Simulate transactions with real-time stock and checkout</p>
          </div>
          <Link href="/products" className="text-sm font-semibold text-indigo-600 hover:text-indigo-500">
            Browse All &rarr;
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-72 rounded-xl bg-slate-200 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
