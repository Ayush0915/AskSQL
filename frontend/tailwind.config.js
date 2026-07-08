/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#3D4550",       // Warm slate page background
        darkCard: "#454E5A",     // Subtly lighter warm slate card background
        textPrimary: "#F5F0E6",  // Warm off-white
        textSecondary: "#C2BAA8",// Muted warm gray
        accentPrimary: "#E8B923",// Yellow/gold
        accentPrimaryHover: "#C99A16", // Darker gold
        accentSecondary: "#C1443A", // Warm red
        successGreen: "#4ADE80", // Emerald success color
        errorRed: "#C1443A",     // Warm red error color
        borderSubtle: "rgba(255,255,255,0.08)"
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"]
      }
    },
  },
  plugins: [],
}
