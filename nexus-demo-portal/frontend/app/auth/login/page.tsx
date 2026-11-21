"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { User, Lock, ArrowRight } from "lucide-react";
import { apiRequest } from "@/lib/api-client";
import { useCart } from "@/lib/cart-context";

export default function LoginPage() {
  const router = useRouter();
  const { setUserSession } = useCart();
  const [email, setEmail] = useState("shopper@example.com");
  const [password, setPassword] = useState("ShopperPassword2026!");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const res = await apiRequest<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    setSubmitting(false);

    if (res.success && res.data) {
      setUserSession(res.data.user, res.data.access_token);
      router.push("/products");
    } else {
      setError(res.error?.message || res.message || "Invalid credentials.");
    }
  };

  return (
    <div className="flex min-h-[75vh] items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Sign In to Your Account</h2>
          <p className="text-xs text-slate-500">Access your cart, order history, and test user journeys</p>
        </div>

        {error && (
          <div className="rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-indigo-600 py-2.5 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            {submitting ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          Don't have an account?{" "}
          <Link href="/auth/register" className="font-semibold text-indigo-600 hover:text-indigo-500">
            Create one here
          </Link>
        </div>
      </div>
    </div>
  );
}
