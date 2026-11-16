import type { Config } from "tailwindcss";

const withAlpha = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: withAlpha("background"),
        surface: withAlpha("surface"),
        card: withAlpha("card"),
        primary: {
          DEFAULT: withAlpha("primary"),
          hover: withAlpha("primary-hover"),
          foreground: withAlpha("primary-foreground"),
        },
        ink: withAlpha("ink"),
        accent: { DEFAULT: withAlpha("accent"), foreground: withAlpha("background") },
        success: withAlpha("success"),
        warning: withAlpha("warning"),
        danger: withAlpha("danger"),
        foreground: withAlpha("foreground"),
        muted: withAlpha("muted"),
        border: withAlpha("border"),
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.375rem",
      },
      boxShadow: {
        card: "0 1px 2px rgb(var(--shadow-color) / 0.05), 0 1px 3px rgb(var(--shadow-color) / 0.04)",
        lift: "0 8px 24px -6px rgb(var(--shadow-color) / 0.12)",
      },
      fontFamily: {
        heading: ["Space Grotesk", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.15s ease-out",
        "slide-up": "slide-up 0.2s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
