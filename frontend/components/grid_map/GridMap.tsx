"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  SUBSTATION_COORDS,
  TRANSMISSION_LINES,
  getStatusColor,
} from "@/lib/utils";
import { useTheme } from "@/components/ui/ThemeProvider";

interface GridMapProps {
  transformers: any[];
  regions: any[];
  filters: any;
}

/**
 * GridPulse project regions.
 * "All Regions" is a UI option, NOT an actual geographic region.
 */
const GRID_REGIONS = ["North", "South", "East", "West"] as const;

type GridRegion = (typeof GRID_REGIONS)[number];

/**
 * Simplified India boundary.
 * Fill remains transparent so it does not create the gray polygon
 * that was previously visible in dark mode.
 */
const INDIA_GEOJSON = {
  type: "FeatureCollection" as const,
  features: [
    {
      type: "Feature" as const,
      properties: { name: "India" },
      geometry: {
        type: "Polygon" as const,
        coordinates: [
          [
            [68.0, 8.0],
            [72.0, 8.0],
            [77.0, 8.5],
            [80.0, 10.0],
            [80.5, 13.0],
            [80.0, 16.0],
            [80.5, 17.5],
            [82.0, 18.5],
            [84.0, 20.0],
            [86.0, 22.0],
            [88.0, 22.0],
            [89.0, 22.0],
            [89.5, 26.0],
            [92.0, 26.5],
            [97.0, 28.0],
            [97.5, 28.5],
            [97.0, 30.0],
            [95.0, 30.0],
            [92.0, 28.0],
            [89.0, 28.0],
            [88.0, 28.0],
            [86.0, 27.0],
            [84.0, 27.0],
            [82.0, 27.5],
            [81.0, 30.0],
            [80.0, 31.5],
            [79.0, 33.0],
            [77.0, 35.0],
            [75.0, 37.0],
            [73.5, 36.0],
            [72.0, 34.0],
            [71.0, 33.0],
            [70.0, 28.0],
            [68.0, 24.0],
            [66.5, 25.0],
            [68.0, 24.0],
            [68.5, 22.0],
            [72.0, 20.0],
            [72.5, 18.0],
            [73.0, 16.0],
            [73.5, 14.0],
            [74.0, 12.0],
            [74.5, 10.0],
            [72.0, 8.0],
            [68.0, 8.0],
          ],
        ],
      },
    },
  ],
};

export default function GridMap({
  transformers,
  regions,
  filters,
}: GridMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);

  // ------------------------------------------------------------
  // Stable Leaflet references
  // ------------------------------------------------------------
  const mapInstanceRef = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);
  const indiaLayerRef = useRef<any>(null);

  const markersLayerRef = useRef<any>(null);
  const linesLayerRef = useRef<any>(null);

  // Individual marker references.
  // This allows markers to be updated rather than destroying
  // and recreating the entire marker collection.
  const markerRefs = useRef<Map<string, any>>(new Map());

  // Individual transmission line references.
  const lineRefs = useRef<Map<string, any>>(new Map());

  // Last region for which the viewport was fitted.
  const lastFitRegionRef = useRef<string>("__none__");

  // Prevent map resize/update races during initialization.
  const mapReadyRef = useRef(false);

  const [leafletLoaded, setLeafletLoaded] = useState(false);

  const { theme } = useTheme();

  const isDark = theme === "dark";

  /**
   * IMPORTANT:
   * "All Regions" must be treated as no geographic region filter.
   */
  const selectedRegionRaw = filters?.region ?? "";

  const isAllRegions =
    !selectedRegionRaw ||
    selectedRegionRaw === "All Regions";

  const selectedRegion = isAllRegions
    ? ""
    : String(selectedRegionRaw);

  // ------------------------------------------------------------
  // 1. Load Leaflet ONCE
  // ------------------------------------------------------------
  useEffect(() => {
    if (typeof window === "undefined") return;

    if ((window as any).L) {
      setLeafletLoaded(true);
      return;
    }

    const existingLink = document.querySelector(
      'link[data-gridpulse-leaflet="true"]'
    );

    if (!existingLink) {
      const link = document.createElement("link");

      link.rel = "stylesheet";
      link.href =
        "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";

      link.setAttribute("data-gridpulse-leaflet", "true");

      document.head.appendChild(link);
    }

    const existingScript = document.querySelector(
      'script[data-gridpulse-leaflet="true"]'
    );

    if (existingScript) {
      const checkLoaded = () => {
        if ((window as any).L) {
          setLeafletLoaded(true);
        }
      };

      existingScript.addEventListener("load", checkLoaded);

      if ((window as any).L) {
        setLeafletLoaded(true);
      }

      return () => {
        existingScript.removeEventListener("load", checkLoaded);
      };
    }

    const script = document.createElement("script");

    script.src =
      "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

    script.async = true;

    script.setAttribute("data-gridpulse-leaflet", "true");

    script.onload = () => {
      setLeafletLoaded(true);
    };

    document.head.appendChild(script);
  }, []);

  // ------------------------------------------------------------
  // 2. Initialize Leaflet map ONCE
  // ------------------------------------------------------------
  useEffect(() => {
    if (!leafletLoaded) return;
    if (!mapRef.current) return;
    if (mapInstanceRef.current) return;

    const L = (window as any).L;

    if (!L) return;

    const map = L.map(mapRef.current, {
      center: [22.0, 78.0],
      zoom: 5,
      zoomControl: false,
      attributionControl: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      dragging: true,
      touchZoom: true,
      boxZoom: false,
      keyboard: true,
    });

    mapInstanceRef.current = map;
    mapReadyRef.current = true;

    // ----------------------------------------------------------
    // Base map
    // ----------------------------------------------------------
    tileLayerRef.current = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 18,
        minZoom: 4,
        opacity: isDark ? 0.72 : 0.82,
        updateWhenIdle: true,
        keepBuffer: 2,
      }
    ).addTo(map);

    // ----------------------------------------------------------
    // India boundary
    // Transparent fill — boundary only.
    // ----------------------------------------------------------
    indiaLayerRef.current = L.geoJSON(INDIA_GEOJSON, {
      style: () => ({
        fillColor: "transparent",
        fillOpacity: 0,
        color: isDark ? "#64748b" : "#94a3b8",
        weight: 1.5,
        opacity: 0.8,
      }),
    }).addTo(map);

    // ----------------------------------------------------------
    // Dynamic layers
    // ----------------------------------------------------------
    markersLayerRef.current = L.layerGroup().addTo(map);
    linesLayerRef.current = L.layerGroup().addTo(map);

    // ----------------------------------------------------------
    // Keep map correctly sized.
    // ----------------------------------------------------------
    let resizeObserver: ResizeObserver | null = null;

    if (typeof ResizeObserver !== "undefined" && mapRef.current) {
      resizeObserver = new ResizeObserver(() => {
        if (!mapInstanceRef.current) return;

        requestAnimationFrame(() => {
          mapInstanceRef.current?.invalidateSize({
            animate: false,
          });
        });
      });

      resizeObserver.observe(mapRef.current);
    }

    // Make sure Leaflet calculates its initial dimensions
    // after the card has been painted.
    requestAnimationFrame(() => {
      map.invalidateSize({
        animate: false,
      });
    });

    return () => {
      resizeObserver?.disconnect();

      markerRefs.current.clear();
      lineRefs.current.clear();

      mapReadyRef.current = false;

      map.remove();

      mapInstanceRef.current = null;
      tileLayerRef.current = null;
      indiaLayerRef.current = null;
      markersLayerRef.current = null;
      linesLayerRef.current = null;

      lastFitRegionRef.current = "__none__";
    };

    // Intentionally initialize only when Leaflet becomes available.
    // Theme changes and telemetry updates must NOT recreate the map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leafletLoaded]);

  // ------------------------------------------------------------
  // 3. Theme changes — styling only
  // ------------------------------------------------------------
  useEffect(() => {
    const map = mapInstanceRef.current;

    if (!map) return;

    if (tileLayerRef.current) {
      tileLayerRef.current.setOpacity(
        isDark ? 0.72 : 0.82
      );
    }

    if (indiaLayerRef.current) {
      indiaLayerRef.current.setStyle({
        fillColor: "transparent",
        fillOpacity: 0,
        color: isDark ? "#64748b" : "#94a3b8",
        weight: 1.5,
        opacity: 0.8,
      });
    }

    /**
     * Do NOT recreate the map for dark mode.
     *
     * A subtle CSS filter darkens the light OSM tiles without
     * introducing a gray polygon overlay.
     */
    const tilePane = map.getPane("tilePane");

    if (tilePane) {
      tilePane.style.filter = isDark
        ? "brightness(0.68) saturate(0.72) contrast(1.05)"
        : "none";
    }
  }, [isDark]);

  // ------------------------------------------------------------
  // 4. Aggregate filtered transformer data by substation
  // ------------------------------------------------------------
  const substationAggregates = useMemo(() => {
    const result = new Map<string, any>();

    for (const transformer of transformers || []) {
      const sid = transformer?.substation_id;

      if (!sid) continue;

      let agg = result.get(sid);

      if (!agg) {
        agg = {
          sid,
          count: 0,
          faults: 0,
          load: 0,
          temp: 0,
          riskSum: 0,
          maxRisk: 0,
          status: "Normal",
        };

        result.set(sid, agg);
      }

      agg.count += 1;

      agg.faults += Number(
        transformer?.total_faults ?? 0
      );

      agg.load += Number(
        transformer?.avg_load_percent ?? 0
      );

      agg.temp += Number(
        transformer?.avg_temperature_c ?? 0
      );

      const risk = Number(
        transformer?.avg_risk_score ??
          transformer?.max_risk_score ??
          transformer?.risk_score ??
          0
      );

      agg.riskSum += risk;
      agg.maxRisk = Math.max(agg.maxRisk, risk);

      // Explicit priority:
      // Critical > High Risk > Warning > Normal
      if (risk >= 85) {
        agg.status = "Critical";
      } else if (
        risk >= 70 &&
        agg.status !== "Critical"
      ) {
        agg.status = "High Risk";
      } else if (
        risk >= 50 &&
        agg.status !== "Critical" &&
        agg.status !== "High Risk"
      ) {
        agg.status = "Warning";
      }
    }

    return result;
  }, [transformers]);

  // ------------------------------------------------------------
  // 5. Determine visible substations
  // ------------------------------------------------------------
  const visibleSubstations = useMemo(() => {
    const set = new Set<string>();

    for (const transformer of transformers || []) {
      const sid = transformer?.substation_id;

      if (!sid) continue;

      const info = SUBSTATION_COORDS[sid];

      if (!info) continue;

      /**
       * If a specific region is selected, respect the region
       * from the actual substation coordinate definition.
       */
      if (
        selectedRegion &&
        info.region !== selectedRegion
      ) {
        continue;
      }

      set.add(sid);
    }

    return set;
  }, [transformers, selectedRegion]);

  // ------------------------------------------------------------
  // 6. Update markers and lines WITHOUT recreating the map
  // ------------------------------------------------------------
  useEffect(() => {
    const map = mapInstanceRef.current;
    const L = (window as any).L;

    if (!leafletLoaded || !map || !L) return;
    if (!mapReadyRef.current) return;

    if (!markersLayerRef.current) return;
    if (!linesLayerRef.current) return;

    // ==========================================================
    // MARKERS
    // ==========================================================

    const activeMarkerIds = new Set<string>();

    for (const sid of visibleSubstations) {
      const info = SUBSTATION_COORDS[sid];

      if (!info) continue;

      const agg = substationAggregates.get(sid);

      const status = agg?.status || "Normal";

      const color = getStatusColor(status);

      const radius =
        status === "Critical"
          ? 8
          : status === "High Risk"
          ? 7
          : status === "Warning"
          ? 6
          : 5;

      activeMarkerIds.add(sid);

      let marker = markerRefs.current.get(sid);

      // Create marker ONLY if it doesn't already exist.
      if (!marker) {
        marker = L.circleMarker(
          [info.lat, info.lon],
          {
            radius,
            fillColor: color,
            color: isDark
              ? "#0f172a"
              : "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9,
          }
        );

        marker.addTo(
          markersLayerRef.current
        );

        markerRefs.current.set(sid, marker);
      } else {
        // Update existing marker in place.
        marker.setLatLng([
          info.lat,
          info.lon,
        ]);

        marker.setStyle({
          radius,
          fillColor: color,
          color: isDark
            ? "#0f172a"
            : "#ffffff",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        });
      }

      const avgLoad =
        agg && agg.count
          ? agg.load / agg.count
          : 0;

      const avgTemp =
        agg && agg.count
          ? agg.temp / agg.count
          : 0;

      const avgRisk =
        agg && agg.count
          ? agg.riskSum / agg.count
          : 0;

      marker.bindTooltip(
        `
        <div
          style="
            font-family: Inter, sans-serif;
            font-size: 12px;
            line-height: 1.5;
          "
        >
          <b>${info.name}</b> (${sid})<br>
          Region: ${info.region}<br>
          Status: ${status}<br>
          Transformers: ${agg?.count ?? 0}<br>
          Avg Load: ${avgLoad.toFixed(1)}%<br>
          Avg Temp: ${avgTemp.toFixed(1)}°C<br>
          Avg Risk: ${avgRisk.toFixed(1)}<br>
          Faults: ${agg?.faults ?? 0}
        </div>
        `,
        {
          direction: "top",
          offset: [0, -8],
        }
      );
    }

    // Remove only markers that are no longer visible.
    for (const [sid, marker] of markerRefs.current) {
      if (!activeMarkerIds.has(sid)) {
        markersLayerRef.current.removeLayer(
          marker
        );

        markerRefs.current.delete(sid);
      }
    }

    // ==========================================================
    // TRANSMISSION LINES
    // ==========================================================

    const activeLineIds = new Set<string>();

    for (const [index, connection] of TRANSMISSION_LINES.entries()) {
      const [from, to] = connection;

      /**
       * Only display a transmission line when both endpoints
       * belong to the current filtered visible substations.
       */
      if (
        visibleSubstations.size > 0 &&
        (!visibleSubstations.has(from) ||
          !visibleSubstations.has(to))
      ) {
        continue;
      }

      const fromInfo = SUBSTATION_COORDS[from];
      const toInfo = SUBSTATION_COORDS[to];

      if (!fromInfo || !toInfo) continue;

      const lineId = `${from}-${to}-${index}`;

      activeLineIds.add(lineId);

      let line = lineRefs.current.get(lineId);

      const lineOptions = {
        color: isDark
          ? "#60a5fa"
          : "#2563eb",
        weight: 1.5,
        opacity: 0.5,
        dashArray: "5, 10",
        interactive: false,
      };

      if (!line) {
        line = L.polyline(
          [
            [fromInfo.lat, fromInfo.lon],
            [toInfo.lat, toInfo.lon],
          ],
          lineOptions
        );

        line.addTo(
          linesLayerRef.current
        );

        lineRefs.current.set(
          lineId,
          line
        );
      } else {
        line.setLatLngs([
          [fromInfo.lat, fromInfo.lon],
          [toInfo.lat, toInfo.lon],
        ]);

        line.setStyle(lineOptions);
      }
    }

    // Remove obsolete transmission lines.
    for (const [lineId, line] of lineRefs.current) {
      if (!activeLineIds.has(lineId)) {
        linesLayerRef.current.removeLayer(
          line
        );

        lineRefs.current.delete(lineId);
      }
    }

    // ==========================================================
    // IMPORTANT:
    // NO fitBounds here on normal telemetry updates.
    // Viewport is handled separately below.
    // ==========================================================

  }, [
    leafletLoaded,
    visibleSubstations,
    substationAggregates,
    isDark,
  ]);

  // ------------------------------------------------------------
  // 7. Stable viewport handling
  //
  // This effect ONLY reacts to region changes.
  // Telemetry updates do not change the viewport.
  // ------------------------------------------------------------
  useEffect(() => {
    const map = mapInstanceRef.current;

    if (!leafletLoaded || !map) return;

    /**
     * Region key:
     *
     * "" = All Regions
     */
    const fitKey =
      selectedRegion || "All Regions";

    /**
     * If this exact region has already been fitted,
     * do nothing.
     */
    if (
      lastFitRegionRef.current === fitKey
    ) {
      return;
    }

    const coords: [number, number][] = [];

    // ==========================================================
    // SPECIFIC REGION
    // ==========================================================
    if (selectedRegion) {
      for (const [sid, info] of Object.entries(
        SUBSTATION_COORDS
      )) {
        if (
          info.region === selectedRegion
        ) {
          coords.push([
            info.lat,
            info.lon,
          ]);
        }
      }

      /**
       * Prefer coordinates from actual filtered assets.
       * If available, this keeps the map consistent with
       * the current dataset.
       */
      const filteredCoords: [number, number][] =
        [];

      for (const sid of visibleSubstations) {
        const info =
          SUBSTATION_COORDS[sid];

        if (!info) continue;

        if (
          info.region === selectedRegion
        ) {
          filteredCoords.push([
            info.lat,
            info.lon,
          ]);
        }
      }

      if (filteredCoords.length > 0) {
        coords.length = 0;
        coords.push(...filteredCoords);
      }
    }

    // ==========================================================
    // ALL REGIONS
    // ==========================================================
    else {
      /**
       * IMPORTANT:
       *
       * Use actual GridPulse substations.
       *
       * Do NOT fit to the entire OSM/world map.
       * Do NOT fit to GeoJSON.
       */
      for (const sid of visibleSubstations) {
        const info =
          SUBSTATION_COORDS[sid];

        if (!info) continue;

        coords.push([
          info.lat,
          info.lon,
        ]);
      }

      /**
       * If filtered data is temporarily empty,
       * use all GridPulse substation coordinates.
       *
       * This guarantees that All Regions remains
       * India-focused instead of falling back to
       * the world.
       */
      if (coords.length === 0) {
        for (const info of Object.values(
          SUBSTATION_COORDS
        )) {
          coords.push([
            info.lat,
            info.lon,
          ]);
        }
      }
    }

    if (coords.length === 0) {
      return;
    }

    // ----------------------------------------------------------
    // Calculate bounds from GridPulse coordinates only.
    // ----------------------------------------------------------
    const lats = coords.map(
      (coord) => coord[0]
    );

    const lons = coords.map(
      (coord) => coord[1]
    );

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    /**
     * Apply modest padding.
     *
     * This is intentionally based on the actual
     * GridPulse coordinates rather than the world map.
     */
    const latPadding = Math.max(
      (maxLat - minLat) * 0.08,
      0.7
    );

    const lonPadding = Math.max(
      (maxLon - minLon) * 0.08,
      0.7
    );

    map.fitBounds(
      [
        [
          minLat - latPadding,
          minLon - lonPadding,
        ],
        [
          maxLat + latPadding,
          maxLon + lonPadding,
        ],
      ],
      {
        padding: [24, 24],
        maxZoom: selectedRegion
          ? 8
          : 6,
        animate: false,
      }
    );

    lastFitRegionRef.current =
      fitKey;

  }, [
    leafletLoaded,
    selectedRegion,
    visibleSubstations,
  ]);

  // ------------------------------------------------------------
  // 8. Map counters
  // ------------------------------------------------------------

  /**
   * Only the five project regions should be counted.
   *
   * "All Regions" is not counted as a sixth region.
   */
  const regionSet = useMemo(() => {
    const set = new Set<string>();

    for (const transformer of transformers || []) {
      const region = transformer?.region;

      if (
        region &&
        GRID_REGIONS.includes(
          region as GridRegion
        )
      ) {
        set.add(region);
      }
    }

    return set;
  }, [transformers]);

  const totalRegions =
    regionSet.size ||
    (isAllRegions
      ? Math.min(
          GRID_REGIONS.length,
          regions?.length || 0
        )
      : selectedRegion
      ? 1
      : 0);

  const totalSubstations =
    new Set(
      (transformers || [])
        .map(
          (t: any) =>
            t?.substation_id
        )
        .filter(Boolean)
    ).size;

  /**
   * IMPORTANT:
   *
   * This assumes `transformers` contains one aggregated
   * row per transformer, as expected by the existing API.
   *
   * If the API returns raw telemetry records instead,
   * the backend should provide a unique transformer count.
   */
  const totalTransformersCount =
    new Set(
      (transformers || [])
        .map(
          (t: any) =>
            t?.transformer_id
        )
        .filter(Boolean)
    ).size;

  /**
   * "Active" should not simply mean "not Critical".
   *
   * Prefer explicit active/is_active fields if supplied
   * by the backend.
   *
   * Otherwise fall back to non-critical for compatibility
   * with the existing API.
   */
  const activeCount = (
    transformers || []
  ).filter((t: any) => {
    if (
      typeof t?.is_active ===
      "boolean"
    ) {
      return t.is_active;
    }

    if (
      typeof t?.active ===
      "boolean"
    ) {
      return t.active;
    }

    return (
      (t?.status ||
        t?.worst_status) !==
      "Critical"
    );
  }).length;

  const faultCount = (
    transformers || []
  ).reduce(
    (
      sum: number,
      transformer: any
    ) =>
      sum +
      Number(
        transformer?.total_faults ??
          0
      ),
    0
  );

  // ------------------------------------------------------------
  // 9. Render
  // ------------------------------------------------------------
  return (
    <div
      className="gp-card p-4"
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-[14px] font-semibold text-[var(--gp-text)]">
            Live Grid Map
          </div>

          <div className="text-[11px] text-[var(--gp-text-muted)]">
            Real-time power flow and equipment status
          </div>
        </div>

        <div className="text-right space-y-0.5">
          <div className="text-[11px]">
            <span className="text-[var(--gp-text-muted)]">
              Regions
            </span>

            <span className="text-[var(--gp-text)] font-semibold ml-2">
              {totalRegions}
            </span>
          </div>

          <div className="text-[11px]">
            <span className="text-[var(--gp-text-muted)]">
              Substations
            </span>

            <span className="text-[var(--gp-text)] font-semibold ml-2">
              {totalSubstations}
            </span>
          </div>

          <div className="text-[11px]">
            <span className="text-[var(--gp-text-muted)]">
              Transformers
            </span>

            <span className="text-[var(--gp-text)] font-semibold ml-2">
              {totalTransformersCount}
            </span>
          </div>

          <div className="text-[11px]">
            <span className="text-[var(--gp-text-muted)]">
              Active
            </span>

            <span className="text-green-400 font-semibold ml-2">
              {activeCount}
            </span>
          </div>

          <div className="text-[11px]">
            <span className="text-[var(--gp-text-muted)]">
              Faults
            </span>

            <span className="text-red-400 font-semibold ml-2">
              {faultCount}
            </span>
          </div>
        </div>
      </div>

      {/* Map */}
      <div
        ref={mapRef}
        className="relative rounded-lg overflow-hidden border border-[var(--gp-border)] flex-1"
        style={{
          minHeight: 0,
          background: isDark
            ? "#0f172a"
            : "#f0f0f0",
        }}
      />

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 px-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
          <span className="text-[11px] text-[var(--gp-text-muted)]">
            Normal
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
          <span className="text-[11px] text-[var(--gp-text-muted)]">
            Warning
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-orange-500" />
          <span className="text-[11px] text-[var(--gp-text-muted)]">
            High Risk
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <span className="text-[11px] text-[var(--gp-text-muted)]">
            Critical
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="w-4 h-0 border-t border-dotted border-blue-500 opacity-50" />
          <span className="text-[11px] text-[var(--gp-text-muted)]">
            Transmission Line
          </span>
        </div>
      </div>
    </div>
  );
}