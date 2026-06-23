import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        idbi: {
          blue: "#003087",
          gold: "#C8A951",
          light: "#E8F0FE",
        },
      },
      fontFamily: {
        sans: ["Inter", "Noto Sans Devanagari", "Noto Sans Tamil", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
