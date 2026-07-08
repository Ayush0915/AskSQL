/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0f172a",       // Sleek slate-900 background
        darkCard: "#1e293b",     // Slate-800 card background
        neonAccent: "#38bdf8",   // Sky-400 accent color
        neonPurple: "#a855f7",   // Purple-500 secondary
        successGreen: "#10b981", // Emerald-500 status color
        errorRed: "#ef4444"      // Red-500 status color
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"]
      }
    },
  },
  plugins: [],
}
