import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep slate "operations console" palette — deliberately not a generic
        // SaaS blue/white dashboard.
        ink: {
          950: "#070a12",
          900: "#0b1020",
          850: "#0f1526",
          800: "#141b30",
          700: "#1c2540",
          600: "#26304f",
          500: "#3a466b",
        },
        severity: {
          high: "#f0476b",
          medium: "#f5a524",
          low: "#3aa0ff",
          ok: "#2dd4a7",
        },
        accent: {
          DEFAULT: "#5b8cff",
          soft: "#8fb0ff",
        },
      },
      fontFamily: {
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 30px rgba(0,0,0,0.35)",
        glow: "0 0 0 1px rgba(91,140,255,0.35), 0 0 24px rgba(91,140,255,0.25)",
      },
      keyframes: {
        pulseline: {
          "0%,100%": { opacity: "0.35" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        pulseline: "pulseline 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
