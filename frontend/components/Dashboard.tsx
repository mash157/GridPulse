"use client";

import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import KPICards from "@/components/kpi/KPICards";
import GridMap from "@/components/grid_map/GridMap";
import {
  GridHealthDonut,
  EnergyByRegion,
  TopAnomalyTypes,
  PowerGenerationConsumption,
} from "@/components/charts/Charts";
import GridRiskLandscape3D from "@/components/charts3d/GridRiskLandscape3D";
import TransformerTable from "@/components/tables/TransformerTable";
import RecentAlerts from "@/components/alerts/RecentAlerts";
import LiveFeed from "@/components/LiveFeed";

export default function Dashboard() {
  const {
    summary,
    regions,
    transformers,
    anomalies,
    energy,
    gridHealth,
    risk,
    analytics3D,
    alerts,
    filters,
    loading,
    error,
    updateFilter,
    clearFilters,
    energyTimeRange,
    setEnergyTimeRange,
    powerTimeRange,
    setPowerTimeRange,
  } = useGridData();

  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      {/* Sidebar */}
      <Sidebar
        filters={filters}
        updateFilter={updateFilter}
        clearFilters={clearFilters}
        systemStatus={summary}
        anomalyCount={summary?.anomalies_detected || 0}
      />

      {/* Main Content */}
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />

        {/* Dashboard Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-[13px] text-red-400">
              {error} — Showing fallback data
            </div>
          )}

          {/* KPI Cards */}
          <KPICards summary={summary} />

          {/* Row 1: Map (left 6/12) + 4 panels on right (6/12) */}
          <div className="grid grid-cols-12 gap-4">
            {/* Live Grid Map - spans left half */}
            <div className="col-span-6">
              <GridMap transformers={transformers} regions={regions} filters={filters} />
            </div>

            {/* Right side: 2 columns x 2 rows */}
            <div className="col-span-6 grid grid-cols-2 gap-4">
              {/* Top-left: Grid Health Distribution */}
              <GridHealthDonut gridHealth={gridHealth} regions={regions} />

              {/* Top-right: Energy by Region */}
              <EnergyByRegion
                regions={regions}
                timeRange={energyTimeRange}
                onTimeRangeChange={setEnergyTimeRange}
              />

              {/* Bottom-left: Top Anomaly Types */}
              <TopAnomalyTypes anomalies={anomalies} />

              {/* Bottom-right: Top Risk Transformers */}
              <TransformerTable transformers={transformers} />
            </div>
          </div>

          {/* Row 2: Power Gen vs Consumption | 3D Analytics | Recent Alerts
              Equal-height cards via .bottom-grid */}
          <div className="bottom-grid">
            <PowerGenerationConsumption
              hourly={energy?.hourly || []}
              timeRange={powerTimeRange}
              onTimeRangeChange={setPowerTimeRange}
            />
            <GridRiskLandscape3D data3d={analytics3D} />
            <RecentAlerts alerts={alerts} />
          </div>
        </div>

        {/* Live Feed */}
        <LiveFeed events={liveEvents} />
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/20 z-50 flex items-center justify-center">
          <div className="bg-[var(--gp-surface)] rounded-xl p-6 shadow-xl flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-[var(--gp-primary)] border-t-transparent rounded-full animate-spin" />
            <span className="text-[14px] text-[var(--gp-text)]">Loading dashboard...</span>
          </div>
        </div>
      )}
    </div>
  );
}
