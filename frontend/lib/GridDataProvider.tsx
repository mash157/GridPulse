"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode,
} from "react";
import { api } from "@/lib/api";
import type { FilterState } from "@/types/gridpulse";

const DEFAULT_FILTERS: FilterState = {
  region: "",
  substation: "",
  transformer: "",
  status: "",
  anomalyTypes: [],
  riskLevel: "",
  // Default to the full dataset window (90d) so every chart, counter, and
  // the anomaly badge reflect the complete 150,000-record distribution.
  timeRange: "90d",
};

interface GridDataContextType {
  summary: any;
  regions: any[];
  transformers: any[];
  anomalies: any[];
  energy: any;
  gridHealth: any;
  risk: any;
  analytics3D: any;
  alerts: any[];
  filters: FilterState;
  loading: boolean;
  error: string | null;
  updateFilter: (key: keyof FilterState, value: string | string[]) => void;
  clearFilters: () => void;
  refresh: () => void;
  energyTimeRange: string;
  setEnergyTimeRange: (v: string) => void;
  powerTimeRange: string;
  setPowerTimeRange: (v: string) => void;
}

const GridDataContext = createContext<GridDataContextType | null>(null);

export function useGridData(): GridDataContextType {
  const ctx = useContext(GridDataContext);
  if (!ctx) {
    return {
      summary: null,
      regions: [],
      transformers: [],
      anomalies: [],
      energy: null,
      gridHealth: null,
      risk: null,
      analytics3D: null,
      alerts: [],
      filters: DEFAULT_FILTERS,
      loading: true,
      error: null,
      updateFilter: () => {},
      clearFilters: () => {},
      refresh: () => {},
      energyTimeRange: "90d",
      setEnergyTimeRange: () => {},
      powerTimeRange: "90d",
      setPowerTimeRange: () => {},
    };
  }
  return ctx;
}

export function GridDataProvider({ children }: { children: ReactNode }) {
  const [summary, setSummary] = useState<any>(null);
  const [regions, setRegions] = useState<any[]>([]);
  const [transformers, setTransformers] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [energy, setEnergy] = useState<any>(null);
  const [gridHealth, setGridHealth] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [analytics3D, setAnalytics3D] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [energyTimeRange, setEnergyTimeRange] = useState("90d");
  const [powerTimeRange, setPowerTimeRange] = useState("90d");

  // Use a ref to track the latest filter params to avoid stale closures
  const filtersRef = useRef(filters);
  filtersRef.current = filters;
  const energyTimeRangeRef = useRef(energyTimeRange);
  energyTimeRangeRef.current = energyTimeRange;
  const powerTimeRangeRef = useRef(powerTimeRange);
  powerTimeRangeRef.current = powerTimeRange;

  const buildFilterParams = useCallback((overrideFilters?: FilterState) => {
    const f = overrideFilters || filtersRef.current;
    const params: Record<string, string> = {};
    if (f.region) params.region = f.region;
    if (f.substation) params.substation = f.substation;
    if (f.transformer) params.transformer = f.transformer;
    if (f.status) params.status = f.status;
    // Multi-select anomaly types: join as comma-separated string
    if (f.anomalyTypes && f.anomalyTypes.length > 0) {
      params.anomaly_type = f.anomalyTypes.join(",");
    }
    if (f.riskLevel) params.risk_level = f.riskLevel;
    if (f.timeRange) params.time_range = f.timeRange;
    return params;
  }, []);

  const fetchAll = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);

      const fp = buildFilterParams();
      const energyTime = energyTimeRangeRef.current;
      const powerTime = powerTimeRangeRef.current;

      // Energy uses its own time range; regions use global time range
      const energyFp = { ...fp, time_range: energyTime };
      const regionsFp = { ...fp }; // Uses global time range

      const [sum, reg, trans, anom, en, gh, r, a3d, al] =
        await Promise.allSettled([
          api.getSummary(fp),
          api.getRegions(regionsFp),
          api.getTransformers(fp),
          api.getAnomalies(fp),
          api.getEnergy(energyFp),
          api.getGridHealth(fp),
          api.getRisk(fp),
          api.getAnalytics3D(fp),
          api.getAlerts(fp),
        ]);

      if (sum.status === "fulfilled") setSummary(sum.value as any);
      if (reg.status === "fulfilled") setRegions((reg.value as any[]) || []);
      if (trans.status === "fulfilled") setTransformers((trans.value as any[]) || []);
      if (anom.status === "fulfilled") setAnomalies((anom.value as any[]) || []);
      if (en.status === "fulfilled") setEnergy(en.value as any);
      if (gh.status === "fulfilled") setGridHealth(gh.value as any);
      if (r.status === "fulfilled") setRisk(r.value as any);
      if (a3d.status === "fulfilled") setAnalytics3D(a3d.value as any);
      if (al.status === "fulfilled") setAlerts((al.value as any[]) || []);
    } catch (e: any) {
      setError(e.message || "Failed to load dashboard data");
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [buildFilterParams]);

  // Re-fetch ALL data when any global filter changes
  useEffect(() => {
    fetchAll(true);
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  // When energy chart time range changes, re-fetch energy + regions only
  useEffect(() => {
    const fp = buildFilterParams();
    const energyFp = { ...fp, time_range: energyTimeRange };
    Promise.allSettled([
      api.getEnergy(energyFp),
      api.getRegions(energyFp),
    ]).then(([en, reg]) => {
      if (en.status === "fulfilled") setEnergy(en.value as any);
      if (reg.status === "fulfilled") setRegions((reg.value as any[]) || []);
    });
  }, [energyTimeRange]); // eslint-disable-line react-hooks/exhaustive-deps

  // When power chart time range changes, re-fetch energy only
  useEffect(() => {
    const fp = buildFilterParams();
    const powerFp = { ...fp, time_range: powerTimeRange };
    api.getEnergy(powerFp).then((result) => {
      setEnergy(result as any);
    }).catch(() => {});
  }, [powerTimeRange]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateFilter = useCallback(
    (key: keyof FilterState, value: string | string[]) => {
      setFilters((prev) => ({ ...prev, [key]: value } as FilterState));
    },
    []
  );

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setEnergyTimeRange("90d");
    setPowerTimeRange("90d");
  }, []);

  const value: GridDataContextType = {
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
    refresh: () => fetchAll(true),
    energyTimeRange,
    setEnergyTimeRange,
    powerTimeRange,
    setPowerTimeRange,
  };

  return (
    <GridDataContext.Provider value={value}>{children}</GridDataContext.Provider>
  );
}
