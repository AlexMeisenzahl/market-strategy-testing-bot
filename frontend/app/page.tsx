"use client";

import React, { useEffect, useState } from "react";
import { StatusCard } from "@/components/StatusCard";
import { EquityChart } from "@/components/EquityChart";
import { TradesTable } from "@/components/TradesTable";
import { StrategyCards } from "@/components/StrategyCards";
import { AlertsPanel } from "@/components/AlertsPanel";
import {
  fetchStatus,
  fetchPerformance,
  fetchTrades,
  fetchStrategies,
  fetchLogs,
} from "@/lib/api";
import type { ApiStatus, ApiPerformance, Trade, EquityPoint } from "@/types";

function buildEquityCurve(trades: Trade[], currentEquity: number): EquityPoint[] {
  const closed = trades
    .filter((t) => t.lifecycle !== "OPEN" && t.pnl_usd != null)
    .map((t) => ({
      time: t.exit_time || t.entry_time || "",
      pnl: Number(t.pnl_usd),
    }))
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

  if (closed.length === 0) {
    return [{ time: "—", equity: currentEquity, cumulativePnl: 0 }];
  }

  const totalPnl = closed.reduce((sum, t) => sum + t.pnl, 0);
  let cumulative = 0;
  const points: EquityPoint[] = [];
  for (const t of closed) {
    cumulative += t.pnl;
    points.push({
      time: t.time,
      equity: currentEquity - totalPnl + cumulative,
      cumulativePnl: cumulative,
    });
  }
  return points;
}

export default function DashboardPage() {
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [performance, setPerformance] = useState<ApiPerformance | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [strategies, setStrategies] = useState<import("@/types").Strategy[]>([]);
  const [logs, setLogs] = useState<import("@/types").LogEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [perfError, setPerfError] = useState<string | null>(null);
  const [tradesError, setTradesError] = useState<string | null>(null);
  const [strategiesError, setStrategiesError] = useState<string | null>(null);
  const [logsError, setLogsError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setStatusError(null);
      setPerfError(null);
      setTradesError(null);
      setStrategiesError(null);
      setLogsError(null);

      const [s, p, t, st, l] = await Promise.all([
        fetchStatus(),
        fetchPerformance(),
        fetchTrades(),
        fetchStrategies(),
        fetchLogs(),
      ]);

      if (!mounted) return;

      if (s.loading === false) {
        if (s.error) setStatusError(s.error);
        else if (s.data) setStatus(s.data);
      }
      if (p.loading === false) {
        if (p.error) setPerfError(p.error);
        else if (p.data) setPerformance(p.data);
      }
      if (t.loading === false) {
        if (t.error) setTradesError(t.error);
        else if (t.data) setTrades(t.data.trades);
      }
      if (st.loading === false) {
        if (st.error) setStrategiesError(st.error);
        else if (st.data) setStrategies(st.data.strategies);
      }
      if (l.loading === false) {
        if (l.error) setLogsError(l.error);
        else if (l.data) setLogs(l.data.events);
      }
      setLoading(false);
    }

    load();
    const interval = setInterval(load, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const equity = status?.equity ?? 0;
  const equityCurveData = buildEquityCurve(trades, equity);

  return (
    <main className="min-h-screen bg-slate-950 p-4 md:p-6">
      <header className="mb-6 border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-slate-100">Market Strategy Bot</h1>
        <p className="mt-1 text-sm text-slate-400">Trading dashboard</p>
      </header>

      {/* Top row: Total Equity, Today PnL, Open Positions, Win Rate, Engine Status */}
      <section className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <StatusCard
          title="Total Equity"
          value={loading && !status ? "—" : `$${Number(equity).toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
          variant={statusError ? "muted" : "default"}
        />
        <StatusCard
          title="Today PnL"
          value={
            loading && !performance
              ? "—"
              : `$${Number(performance?.daily_pnl ?? 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}`
          }
          variant={
            perfError
              ? "muted"
              : (performance?.daily_pnl ?? 0) >= 0
                ? "success"
                : "danger"
          }
        />
        <StatusCard
          title="Open Positions"
          value={loading && !status ? "—" : String(status?.active_positions ?? 0)}
          variant={statusError ? "muted" : "default"}
        />
        <StatusCard
          title="Win Rate"
          value={
            loading && !performance
              ? "—"
              : `${Number(performance?.win_rate ?? 0).toFixed(1)}%`
          }
          variant={perfError ? "muted" : "default"}
        />
        <StatusCard
          title="Engine Status"
          value={loading && !status ? "—" : String(status?.engine_status ?? "unknown")}
          subtitle={status?.connected ? "Connected" : "Disconnected"}
          variant={
            statusError
              ? "muted"
              : status?.engine_status === "running"
                ? "success"
                : status?.engine_status === "paused"
                  ? "warning"
                  : "default"
          }
        />
      </section>

      {/* Middle: full-width Equity curve */}
      <section className="mb-6">
        <EquityChart
          data={equityCurveData}
          currentEquity={equity}
          loading={loading && trades.length === 0 && !tradesError}
        />
      </section>

      {/* Lower grid: Trades table (left), Alerts (right) */}
      <section className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TradesTable
            trades={trades}
            loading={loading && !tradesError && !trades.length}
            error={tradesError}
          />
        </div>
        <div>
          <AlertsPanel
            events={logs}
            loading={loading && !logsError && !logs.length}
            error={logsError}
          />
        </div>
      </section>

      {/* Bottom: Strategy performance cards */}
      <section>
        <StrategyCards
          strategies={strategies}
          loading={loading && !strategiesError && !strategies.length}
          error={strategiesError}
        />
      </section>
    </main>
  );
}
