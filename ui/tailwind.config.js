/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'slate-dark': '#1e1e2e',
        'slate-dark-hover': '#282840',
        'slate-dark-active': '#323250',
        'teal-accent': '#14b8a6',
      },
    },
  },
  plugins: [],
}
