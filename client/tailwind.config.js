/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Enable dark mode
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,vue}",
  ],
  theme: {
    extend: {
      // set custom colors for tailwind
      colors: {
       'accent-primary': '#7461A8',
       'accent-primary-light': '#9688bd',
       'accent-secondary': '#60ACAD',
       'accent-secondary-light': '#9dc6c7',
      }
    }
  },
  plugins: [],
}

