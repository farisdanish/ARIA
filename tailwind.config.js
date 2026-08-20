/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./aria-app/website/templates/**/*.html",
    "./aria-app/website/static/**/*.js",
    "./website/templates/**/*.html",
    "./website/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'aria-bg': '#f4f7fb',
        'aria-surface': '#ffffff',
        'aria-surface-soft': '#eef3fb',
        'aria-text': '#172033',
        'aria-text-muted': '#4c5a73',
        'aria-primary': '#0d4f8c',
        'aria-primary-strong': '#08335a',
        'aria-accent': '#1f9d8b',
        'aria-danger': '#b42318',
        'aria-warning': '#b54708',
        'aria-border': '#d7deea',
      },
      borderRadius: {
        'aria-sm': '8px',
        'aria-md': '12px',
        'aria-lg': '18px',
      },
      boxShadow: {
        'aria-sm': '0 2px 8px rgba(14, 24, 39, 0.08)',
        'aria-md': '0 8px 26px rgba(14, 24, 39, 0.11)',
      }
    },
  },
  plugins: [],
}
