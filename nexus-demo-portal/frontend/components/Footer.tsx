import Link from "next/link";
import { Activity, ShieldCheck, Heart } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <span className="font-semibold text-slate-900">NEXUS Demo Portal</span>
            <span>&bull;</span>
            <span>CICADA 2026 Hackathon Testbed</span>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-500">
            <div className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-medium">
              <Activity className="h-3.5 w-3.5 animate-pulse" />
              Observability Pipeline Active
            </div>
            <Link href="/simulator" className="hover:text-indigo-600 transition">
              Failure Control Panel
            </Link>
            <Link href="http://localhost:8000/docs" target="_blank" className="hover:text-indigo-600 transition">
              Swagger API Docs
            </Link>
          </div>
        </div>
        <div className="mt-4 text-center text-xs text-slate-400">
          Simulated Dummy E-Commerce Platform. No real payments or shipments are processed.
        </div>
      </div>
    </footer>
  );
}
