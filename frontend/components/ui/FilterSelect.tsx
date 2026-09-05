"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChevronDown, Check } from "lucide-react";

interface FilterSelectProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  icon?: React.ReactNode;
}

export default function FilterSelect({
  label,
  value,
  options,
  onChange,
  icon,
}: FilterSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const selectedLabel =
    options.find((o) => o.value === value)?.label || options[0]?.label || "";

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

  return (
    <div className="relative" ref={containerRef}>
      <label className="text-[11px] text-[var(--gp-sidebar-text)] mb-1 block flex items-center gap-1">
        {icon}
        {label}
      </label>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full rounded-md px-2 py-1.5 text-[12px] text-left flex items-center justify-between gap-1 transition-colors focus:outline-none"
        style={{ background: "var(--gp-sidebar-btn-bg)", border: "1px solid var(--gp-sidebar-btn-border)", color: "var(--gp-sidebar-text)" }}
      >
        <span className="truncate">{selectedLabel}</span>
        <ChevronDown
          className={`w-3 h-3 flex-shrink-0 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div
          className="absolute top-full left-0 right-0 mt-1 rounded-lg shadow-xl border z-[100] max-h-52 overflow-hidden flex flex-col"
          style={{
            background: "var(--gp-surface)",
            borderColor: "var(--gp-border)",
          }}
        >
          {options.length > 5 && (
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
          <div className="overflow-y-auto flex-1">
            {filteredOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                  setSearch("");
                }}
                className="w-full text-left px-3 py-2 text-[12px] flex items-center justify-between transition-colors"
                style={{
                  color: value === option.value ? "var(--gp-primary)" : "var(--gp-text)",
                  background: "transparent",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--gp-surface-2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <span className="truncate">{option.label}</span>
                {value === option.value && (
                  <Check className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "var(--gp-primary)" }} />
                )}
              </button>
            ))}
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
