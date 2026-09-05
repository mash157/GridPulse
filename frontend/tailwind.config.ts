import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        gp: {
          bg: "var(--gp-bg)",
          surface: "var(--gp-surface)",
          "surface-2": "var(--gp-surface-2)",
          "surface-3": "var(--gp-surface-3)",
          border: "var(--gp-border)",
          text: "var(--gp-text)",
          "text-muted": "var(--gp-text-muted)",
          "text-dim": "var(--gp-text-dim)",
          primary: "var(--gp-primary)",
          "primary-soft": "var(--gp-primary-soft)",
          accent: "var(--gp-accent)",
          success: "var(--gp-success)",
          warning: "var(--gp-warning)",
          danger: "var(--gp-danger)",
          info: "var(--gp-info)",
          orange: "var(--gp-orange)",
          cyan: "var(--gp-cyan)",
          purple: "var(--gp-purple)",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.06)",
        "card-lg": "0 4px 6px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1)",
        sidebar: "2px 0 8px rgba(0,0,0,0.15)",
      },
      borderRadius: {
        card: "12px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in": "slideIn 0.2s ease-out",
        ticker: "ticker 30s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        ticker: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
