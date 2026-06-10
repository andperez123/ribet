import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ribet: {
          green: "#A3C957",
          text: "#111111",
          bg: "#F7F7F4",
          card: "#FFFFFF",
          border: "#E8E8E3",
          risk: "#D96B6B",
          muted: "#6B6B66",
          ink: "#1A1A18",
          "ink-soft": "#2A2A26",
          amber: "#D4A24C",
          orange: "#E07B4A",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter-tight)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 4px 24px -4px rgba(17, 17, 17, 0.08)",
        hero: "0 8px 40px -8px rgba(17, 17, 17, 0.18)",
      },
      backgroundImage: {
        "hero-gradient":
          "linear-gradient(135deg, #1A1A18 0%, #2A2A26 55%, #1F2A1A 100%)",
        "locked-frost":
          "linear-gradient(180deg, rgba(247,247,244,0.6) 0%, rgba(247,247,244,0.95) 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
