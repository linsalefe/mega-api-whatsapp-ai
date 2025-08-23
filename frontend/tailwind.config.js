/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        whatsapp: {
          green: '#25D366',
          dark: '#128C7E',
          light: '#DCF8C6',
          gray: '#F0F0F0',
          darkgray: '#303030'
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}