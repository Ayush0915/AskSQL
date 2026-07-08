/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "var(--bg-primary)",       // Warm off-white page background
        darkCard: "var(--bg-card)",     // Light gray card background
        darkCardHover: "var(--bg-card-hover)", // Muted hover state
        textPrimary: "var(--text-primary)",  // Dark charcoal/brown text
        textSecondary: "var(--text-secondary)",// Muted warm gray/brown text
        accentPrimary: "var(--accent-primary)",// Dark gold (for text/links contrast)
        accentPrimaryHover: "var(--accent-hover)", // Dark gold hover
        accentSecondary: "var(--error)", // Warm red / error
        btnGold: "var(--btn-gold)",      // Bright gold (for solid buttons only)
        btnGoldHover: "var(--btn-gold-hover)", // Bright gold hover
        successGreen: "var(--success)", // Green success color
        errorRed: "var(--error)",     // Warm red error color
        borderSubtle: "var(--border-subtle)"  // Thin border color
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"]
      }
    },
  },
  plugins: [],
}
