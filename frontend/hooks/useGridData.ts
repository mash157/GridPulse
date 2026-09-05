"use client";

// Re-export useGridData from the shared GridDataProvider context
// This ensures all pages share the same filter state and data
export { useGridData } from "@/lib/GridDataProvider";
