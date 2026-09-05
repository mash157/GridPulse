"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChevronDown, Check, X } from "lucide-react";

interface MultiSelectFilterProps {
  label: string;
  selected: string[];
  options: { value: string; label: string }[];
  onChange: (values: string[]) => void;
  icon?: React.ReactNode;
  placeholder?: string;
}

export default function MultiSelectFilter({
  label,
  selected,
  options,
  onChange,
  icon,
  placeholder = "All",
}: MultiSelectFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const displayText =
    selected.length === 0
      ? placeholder
      : selected.length === 1
        ? options.find((o) => o.value === selected[0])?.label || selected[0]
        : `${selected.length} selected`;

  const filteredOptions = options.filter((o) =>
    o.label.toLowerCase().includes(search.toLowerCase())
  );

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
      setIsOpen(false);
      setSearch("");
    }
  }, []);

  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [handleClickOutside]);

  useEffect(() => {
    if (isOpen && searchRef.current) {
      searchRef.current.focus();
    }
  }, [isOpen]);

  const toggleOption = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  const clearAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  const selectAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(options.map((o) => o.value));
  };

  return (
    <div className="relative" ref={containerRef}>
      <label className="text-[11px] text-[var(--gp-sidebar-text)] mb-1 block flex items-center gap-1">
        {icon}
        {label}
      </label>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full rounded-md px-2 py-1.5 text-[12px] text-left flex items-center justify-between gap-1 transition-colors focus:outline-none"
        style={{
          background: "var(--gp-sidebar-btn-bg)",
          border: "1px solid var(--gp-sidebar-btn-border)",
          color: "var(--gp-sidebar-text)",
        }}
      >
        <span className={`truncate ${selected.length > 0 ? "font-medium" : ""}`}>
          {displayText}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {selected.length > 0 && (
            <X
              className="w-3 h-3 opacity-50 hover:opacity-100 cursor-pointer"
              onClick={clearAll}
            />
          )}
          <ChevronDown
            className={`w-3 h-3 transition-transform ${isOpen ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {isOpen && (
        <div
          className="absolute top-full left-0 right-0 mt-1 rounded-lg shadow-xl border z-[100] max-h-60 overflow-hidden flex flex-col"
          style={{
            background: "var(--gp-surface)",
            borderColor: "var(--gp-border)",
          }}
        >
          {/* Search bar */}
          {options.length > 4 && (
            <div className="p-1 border-b" style={{ borderColor: "var(--gp-border)" }}>
              <input
                ref={searchRef}
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-2 py-1 text-[12px] rounded border focus:outline-none"
                style={{
                  background: "var(--gp-surface-2)",
                  borderColor: "var(--gp-border)",
                  color: "var(--gp-text)",
                }}
              />
            </div>
          )}

          {/* Select All / Clear All */}
          <div
            className="flex items-center gap-2 px-2 py-1.5 border-b text-[11px]"
            style={{ borderColor: "var(--gp-border)" }}
          >
            <button
              onClick={selectAll}
              className="text-[var(--gp-primary)] font-medium hover:underline"
            >
              Select All
            </button>
            <span className="text-[var(--gp-text-dim)]">|</span>
            <button
              onClick={clearAll}
              className="text-[var(--gp-text-dim)] hover:text-[var(--gp-text)] hover:underline"
            >
              Clear
            </button>
          </div>

          {/* Options with checkboxes */}
          <div className="overflow-y-auto flex-1">
            {filteredOptions.map((option) => {
              const isSelected = selected.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() => toggleOption(option.value)}
                  className="w-full text-left px-3 py-2 text-[12px] flex items-center gap-2 transition-colors"
                  style={{
                    color: isSelected ? "var(--gp-primary)" : "var(--gp-text)",
                    background: "transparent",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "var(--gp-surface-2)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                  }}
                >
                  {/* Checkbox */}
                  <div
                    className="w-3.5 h-3.5 rounded border flex-shrink-0 flex items-center justify-center transition-colors"
                    style={{
                      borderColor: isSelected ? "var(--gp-primary)" : "var(--gp-border)",
                      background: isSelected ? "var(--gp-primary)" : "transparent",
                    }}
                  >
                    {isSelected && <Check className="w-2.5 h-2.5 text-white" />}
                  </div>
                  <span className="truncate">{option.label}</span>
                </button>
              );
            })}
            {filteredOptions.length === 0 && (
              <div className="px-3 py-2 text-[12px] text-[var(--gp-text-dim)]">
                No results found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
