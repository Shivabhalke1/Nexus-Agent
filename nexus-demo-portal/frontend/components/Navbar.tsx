"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShoppingBag, ShieldAlert, User, LogOut, Package } from "lucide-react";
import { useCart } from "@/lib/cart-context";

export default function Navbar() {
  const pathname = usePathname();
  const { cart, user, logout } = useCart();
  const totalItems = cart?.total_items || 0;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold shadow-md shadow-indigo-200">
              N
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">
              NEXUS <span className="text-indigo-600">STORE</span>
            </span>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-5 text-sm font-medium">
            <Link
              href="/products"
              className={`transition hover:text-indigo-600 ${
                pathname.startsWith("/products") ? "text-indigo-600 font-semibold" : "text-slate-600"
              }`}
            >
              Catalog
            </Link>
            <Link
              href="/orders"
              className={`transition hover:text-indigo-600 ${
                pathname === "/orders" ? "text-indigo-600 font-semibold" : "text-slate-600"
              }`}
            >
              My Orders
            </Link>
          </nav>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          {/* Simulator Link */}
          <Link
            href="/simulator"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-md hover:bg-amber-100 transition shadow-sm"
          >
            <ShieldAlert className="h-4 w-4 text-amber-600" />
            Failure Simulator
          </Link>

          {/* User Account / Auth */}
          {user ? (
            <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
              <span className="hidden lg:inline text-xs text-slate-600 font-medium">
                {user.full_name}
              </span>
              <button
                onClick={logout}
                title="Logout"
                className="p-2 text-slate-500 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-1 text-xs font-medium text-slate-700 hover:text-indigo-600 border border-slate-200 rounded-lg px-2.5 py-1.5 hover:bg-slate-50 transition"
            >
              <User className="h-4 w-4" />
              Sign In
            </Link>
          )}

          {/* Cart Icon */}
          <Link
            href="/cart"
            className="relative flex items-center justify-center p-2 rounded-lg text-slate-700 hover:text-indigo-600 hover:bg-slate-100 transition"
          >
            <ShoppingBag className="h-5 w-5" />
            {totalItems > 0 && (
              <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-[11px] font-bold text-white shadow">
                {totalItems}
              </span>
            )}
          </Link>
        </div>
      </div>
    </header>
  );
}
