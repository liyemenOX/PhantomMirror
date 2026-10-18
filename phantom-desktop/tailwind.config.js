/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: '#0a0e14',
          card: '#0d121c',
          green: '#00ff66',
        }
      }
    },
  },
  plugins: [],
}
