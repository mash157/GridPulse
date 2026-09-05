"use client";

import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import GridMap from "@/components/grid_map/GridMap";
import LiveFeed from "@/components/LiveFeed";

export default function LiveMapPage() {
  const { transformers, regions, filters, updateFilter, clearFilters, summary } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Live Grid Map</div>
            <div className="section-subtitle">Real-time substation locations, status, and power flow visualization</div>
          </div>
          <div style={{ height: "calc(100vh - 200px)" }}>
            <GridMap transformers={transformers} regions={regions} filters={filters} />
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
