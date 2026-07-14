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
        // IDBI brand tokens — hues are UNCHANGED. The extra keys promote
        // previously-inline hex values to named tokens at identical values
        // (surfaces, gradient stops, mint ramp, risk semantics) so the palette
        // stays intact while gaining a single source of truth.
        idbi: {
          green: "#00836C",   // --dark-green (primary)
          deep: "#036B59",    // darker gradient stop
          dark: "#307360",    // official hover green
          teal: "#4FA9A7",
          orange: "#F37021",  // accent
          orangeDark: "#E0621A",
          light: "#E5F2F0",   // active-nav tint
          // neutral ink scale (subtly green-tinted, saturation kept low)
          ink: "#122622",
          slate: "#3C4E4A",
          muted: "#5B6E69",
          faint: "#9AAAA5",
          line: "rgba(16,40,34,0.08)", // hairline borders
          bg: "#F4F7F6",
          // surfaces (promoted from inline hex)
          surface: "#FAFCFB",    // input bg, card sheen
          surfaceAlt: "#FBFDFC", // insight cards
          tint: "#F1F5F3",       // chat bubble bg, source chips
          track: "#EEF3F1",      // gauge / progress track
          edge: "#E1EAE7",       // neutral divider
          scrollThumb: "#CBD8D4",
          // mint ramp (light-green text/accents on dark surfaces)
          mint: "#BFE6DC",
          mintDim: "#A9DBCC",
          mintBright: "#8FE0C4",
          mintSoft: "#EFF8F4",   // soft gradient stop
          // warm ramp
          peach: "#FDB48A",      // "Seva" wordmark accent
          orangeLight: "#F79B5E",// avatar gradient stop
          warm: "#FFF3E6",
          warmSoft: "#FFF7EE",
          inkGreen: "#0B4C3E",   // dark-green text on mint badge
          gold: "#F5C36B",       // chart palette
          // risk-profile semantics (single source — was duplicated in 2 files)
          risk: {
            conservative: { bg: "#E4F4EC", text: "#1E7A4E" },
            moderate:     { bg: "#FFF3D6", text: "#9A6C00" },
            aggressive:   { bg: "#FDE7DD", text: "#C25A15" },
          },
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Montserrat", "Noto Sans Devanagari", "Noto Sans Tamil", "sans-serif"],
      },
      // Single type scale (collapses ~20 ad-hoc text-[Npx] values).
      fontSize: {
        xs:   ["0.6875rem", { lineHeight: "1.45", letterSpacing: "0.01em" }],  // 11px
        sm:   ["0.8125rem", { lineHeight: "1.5"  }],                           // 13px
        base: ["0.875rem",  { lineHeight: "1.6"  }],                           // 14px
        lg:   ["1.0625rem", { lineHeight: "1.45", letterSpacing: "-0.005em" }],// 17px
        xl:   ["1.375rem",  { lineHeight: "1.35", letterSpacing: "-0.01em" }], // 22px
        "2xl":["1.75rem",   { lineHeight: "1.25", letterSpacing: "-0.02em" }], // 28px
        "3xl":["2.125rem",  { lineHeight: "1.15", letterSpacing: "-0.02em" }], // 34px
      },
      // Named radius tokens — deliberately NOT shadowing rounded-sm/md/lg/xl/2xl,
      // so nothing changes size until a component is migrated. rounded-card (20px)
      // is the hero card radius; the old rounded-[20px]/[18px]/[16px]/[22px]/[24px]
      // all converge here.
      borderRadius: {
        tile:  "10px",
        field: "14px",
        card:  "20px",
        panel: "28px",
        modal: "36px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,40,34,.04), 0 12px 28px -20px rgba(16,40,34,.35)",
        pop: "0 24px 50px -30px rgba(16,40,34,.5)",
        float: "0 -6px 24px -12px rgba(16,40,34,.25)",
        flat: "0 1px 2px rgba(16,40,34,.04)",
        glow: "0 8px 16px -8px rgba(0,131,108,.7)",
        glowOrange: "0 8px 18px -8px rgba(243,112,33,.65)",
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
