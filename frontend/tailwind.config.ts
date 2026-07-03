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
          green: "#00594C",
          dark: "#003D34",
          teal: "#2E9C8F",
          orange: "#EE6C2D",
          light: "#E6F4F1",
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
