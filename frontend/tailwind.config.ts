import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Elegant Light Theme palette
        ink: {
          950: "#ffffff",
          900: "#fafafa",
          850: "#f4f4f5",
          800: "#e4e4e7",
          700: "#d4d4d8",
          600: "#a1a1aa",
          500: "#71717a",
        },
        severity: {
          high: "#e11d48",   // Rose 600
          medium: "#d97706", // Amber 600
          low: "#2563eb",    // Blue 600
          ok: "#059669",     // Emerald 600
        },
        accent: {
          DEFAULT: "#1e3a8a", // Deep Blue 900
          soft: "#3b82f6",    // Blue 500
        },
      },
      fontFamily: {
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        heading: ["var(--font-heading)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 4px 20px rgba(0, 0, 0, 0.04)",
        glow: "0 0 0 1px rgba(30,58,138,0.1), 0 4px 24px rgba(30,58,138,0.08)",
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
