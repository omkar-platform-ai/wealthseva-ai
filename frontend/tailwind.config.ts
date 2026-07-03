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
        // Exact values from idbi.bank.in style.css :root tokens
        idbi: {
          green: "#00836C",
          dark: "#307360",
          teal: "#4FA9A7",
          orange: "#F37021",
          light: "#E5F2F0",
        },
      },
      fontFamily: {
        sans: ["Montserrat", "Noto Sans Devanagari", "Noto Sans Tamil", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
