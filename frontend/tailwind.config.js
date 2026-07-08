/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#FAF6EE",       // Warm off-white page background
        darkCard: "#F3EFE6",     // Light gray card background
        textPrimary: "#2A2620",  // Dark charcoal/brown text
        textSecondary: "#6B5F4F",// Muted warm gray/brown text
        accentPrimary: "#B8860B",// Dark gold (for text/links contrast)
        accentPrimaryHover: "#9E730A", // Dark gold hover
        accentSecondary: "#C1443A", // Warm red
        btnGold: "#E8B923",      // Bright gold (for solid buttons only)
        btnGoldHover: "#C99A16", // Bright gold hover
        successGreen: "#4ADE80", // Emerald success color
        errorRed: "#C1443A",     // Warm red error color
        borderSubtle: "#E5DDD0"  // Thin border color
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"]
      }
    },
  },
  plugins: [],
}
