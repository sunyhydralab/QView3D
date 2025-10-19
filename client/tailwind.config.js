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
        // Light mode colors - super light gray and white
        'light-primary-dark': '#F9FAFB',      // Super light gray for borders/dividers
        'light-primary': '#FAFBFC',           // Almost white for backgrounds
        'light-primary-light': '#FFFFFF',     // Pure white for cards/surfaces

        // Dark mode colors - back to gray instead of blue
        'dark-primary-dark': '#1F2937',       // Dark gray (darkest)
        'dark-primary': '#374151',            // Medium gray
        'dark-primary-light': '#4B5563',      // Lighter gray (lightest dark)

        // Accent colors - vibrant for both modes
        'accent-primary-dark': '#4d3f73',
        'accent-primary': '#7461A8',
        'accent-primary-light': '#9688bd',
        'accent-secondary-darker': '#2f4c4d',
        'accent-secondary-dark': '#48797a',
        'accent-secondary': '#60ACAD',
        'accent-secondary-light': '#9dc6c7',
      }
    }
  },
  plugins: [],
}

