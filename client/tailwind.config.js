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
        'light-primary-dark': '#bdbebf',
        'light-primary': '#E5E7EB',
        'light-primary-light': '#FFFFFF',
        'dark-primary-dark': '#262626',
        'dark-primary': '#333333',
        'dark-primary-light': '#3D3D3D',
        'accent-primary-dark': '#4d3f73',
        'accent-primary': '#7461A8',
        'accent-primary-light': '#9688bd',
        'accent-secondary-dark': '#488687',
        'accent-secondary': '#60ACAD',
        'accent-secondary-light': '#9dc6c7',
      }
    }
  },
  plugins: [],
}

