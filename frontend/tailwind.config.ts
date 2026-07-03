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
        // Exact IDBI brand tokens (idbi.bank.in style.css :root) — unchanged,
        // plus extra shades used by the redesign. Nothing here changes the
        // brand hues; the new keys are neutrals + gradient stops derived from
        // the same palette.
        idbi: {
          green: "#00836C",   // --dark-green  (primary)
          deep: "#036B59",    // darker gradient stop for the primary
          dark: "#307360",    // official hover green
          teal: "#4FA9A7",    // --light-green
          orange: "#F37021",  // --orange
          orangeDark: "#E0621A",
          light: "#E5F2F0",   // active-nav tint
          // neutral ink scale (subtly green-tinted, saturation kept low)
          ink: "#122622",     // headings
          slate: "#3C4E4A",   // body text
          muted: "#5B6E69",   // secondary text
          faint: "#9AAAA5",   // captions / placeholders
          line: "rgba(16,40,34,0.08)", // hairline borders
          bg: "#F4F7F6",      // app background
        },
      },
      fontFamily: {
        sans: ["Montserrat", "Noto Sans Devanagari", "Noto Sans Tamil", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,40,34,.04), 0 12px 28px -20px rgba(16,40,34,.35)",
        pop: "0 24px 50px -30px rgba(16,40,34,.5)",
        float: "0 -6px 24px -12px rgba(16,40,34,.25)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        ping2: {
          "0%": { transform: "scale(1)", opacity: ".55" },
          "100%": { transform: "scale(2.1)", opacity: "0" },
        },
      },
      animation: {
        rise: "rise .5s cubic-bezier(.22,1,.36,1) both",
        ping2: "ping2 1.2s ease-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
