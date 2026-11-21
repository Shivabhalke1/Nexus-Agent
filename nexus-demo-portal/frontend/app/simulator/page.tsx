"use client";

import React, { useEffect, useState } from "react";
import { ShieldAlert, Cpu, Clock, ServerOff, Database, AlertTriangle, Key, RotateCcw, Activity } from "lucide-react";
import { apiRequest } from "@/lib/api-client";

interface ScenarioStatus {
  active: boolean;
  remaining_seconds: number;
  [key: string]: any;
}

export default function SimulatorPage() {
  const [status, setStatus] = useState<Record<string, ScenarioStatus>>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const fetchStatus = async () => {
    const res = await apiRequest<any>("/simulator/status");
    if (res.success && res.data) {
      setStatus(res.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleScenario = async (name: string, shouldActivate: boolean, durationSeconds = 30) => {
    setMessage(null);
    let res;
    if (shouldActivate) {
      res = await apiRequest<any>(`/simulator/scenarios/${name}/activate`, {
        method: "POST",
        body: JSON.stringify({ duration_seconds: durationSeconds }),
      });
    } else {
      res = await apiRequest<any>(`/simulator/scenarios/${name}/deactivate`, {
        method: "POST",
      });
    }

    if (res.success) {
      setMessage(`Scenario '${name}' ${shouldActivate ? "activated" : "deactivated"}.`);
      await fetchStatus();
    } else {
      setMessage(`Failed: ${res.error?.message || res.message}`);
    }
  };

  const handleResetAll = async () => {
    setMessage(null);
    const res = await apiRequest<any>("/simulator/reset", { method: "POST" });
    if (res.success) {
      setMessage("All failure scenarios have been safely stopped.");
      await fetchStatus();
    }
  };

  const scenariosList = [
    {
      id: "high_cpu",
      title: "Scenario 1 — High CPU Utilization",
      desc: "Simulates high computational load spiking CPU utilization for a configured duration.",
      icon: Cpu,
      color: "border-amber-200 bg-amber-50/50",
    },
    {
      id: "slow_api",
      title: "Scenario 2 — Slow API Response",
      desc: "Injects 1500ms artificial latency on catalog endpoints (/api/v1/products).",
      icon: Clock,
      color: "border-blue-200 bg-blue-50/50",
    },
    {
      id: "backend_unavailable",
      title: "Scenario 3 — Backend Unavailable",
      desc: "Simulates backend service failure returning controlled HTTP 503 Service Unavailable.",
      icon: ServerOff,
      color: "border-purple-200 bg-purple-50/50",
    },
    {
      id: "database_failure",
      title: "Scenario 4 — Database Connection Failure",
      desc: "Simulates non-destructive DB outage: makes health probe and product queries fail safely.",
      icon: Database,
      color: "border-rose-200 bg-rose-50/50",
    },
    {
      id: "increased_errors",
      title: "Scenario 5 — Increased Application Errors",
      desc: "Triggers bursts of HTTP 500 Internal Server Errors on targeted catalog endpoints.",
      icon: AlertTriangle,
      color: "border-orange-200 bg-orange-50/50",
    },
    {
      id: "failed_logins",
      title: "Scenario 6 — Repeated Failed Logins",
      desc: "Generates controlled authentication stress test with synthetic accounts without password leakage.",
      icon: Key,
      color: "border-indigo-200 bg-indigo-50/50",
    },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-amber-700 bg-amber-50 border border-amber-200 rounded-full mb-2">
            <ShieldAlert className="h-3.5 w-3.5 text-amber-600" /> Authorized Test Environment
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Controlled Failure Simulator</h1>
          <p className="text-sm text-slate-500 mt-1">
            Trigger safe, non-destructive anomaly scenarios for NEXUS OBSERVE detection validation.
          </p>
        </div>

        <button
          onClick={handleResetAll}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800 transition"
        >
          <RotateCcw className="h-4 w-4" /> Reset All Scenarios
        </button>
      </div>

      {message && (
        <div className="rounded-lg bg-indigo-50 border border-indigo-200 p-3 text-xs font-medium text-indigo-700">
          {message}
        </div>
      )}

      {/* Grid of Scenarios */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {scenariosList.map((sc) => {
          const scState = status[sc.id] || { active: false, remaining_seconds: 0 };
          const Icon = sc.icon;

          return (
            <div
              key={sc.id}
              className={`rounded-2xl border p-6 shadow-sm transition space-y-4 ${sc.color} ${
                scState.active ? "ring-2 ring-amber-500 ring-offset-2" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-white shadow-sm border border-slate-200">
                  <Icon className="h-5 w-5 text-slate-700" />
                </div>
                <span
                  className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${
                    scState.active
                      ? "bg-amber-500 text-white animate-pulse"
                      : "bg-slate-200 text-slate-600"
                  }`}
                >
                  {scState.active ? `ACTIVE (${scState.remaining_seconds}s)` : "INACTIVE"}
                </span>
              </div>

              <div>
                <h3 className="font-bold text-slate-900 text-sm">{sc.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{sc.desc}</p>
              </div>

              <div className="pt-2 border-t border-slate-200/60 flex items-center gap-2">
                {scState.active ? (
                  <button
                    onClick={() => toggleScenario(sc.id, false)}
                    className="w-full rounded-lg bg-rose-600 py-2 text-xs font-semibold text-white shadow-sm hover:bg-rose-700 transition"
                  >
                    Deactivate Scenario
                  </button>
                ) : (
                  <button
                    onClick={() => toggleScenario(sc.id, true, 30)}
                    className="w-full rounded-lg bg-indigo-600 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
                  >
                    Activate (30s Safety Limit)
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Safety Info Callout */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm text-xs text-slate-600 space-y-2">
        <h4 className="font-bold text-slate-900 text-sm">Simulator Safety Guardrails:</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>All scenarios strictly enforce auto-expiration (maximum duration: 300 seconds).</li>
          <li>Database connection failure is simulated non-destructively; no schema or data is altered or deleted.</li>
          <li>High CPU burn utilizes background worker threads and will never deadlock the operating system.</li>
          <li>Synthetic failed login attempts never expose or store real user credentials.</li>
        </ul>
      </div>
    </div>
  );
}
