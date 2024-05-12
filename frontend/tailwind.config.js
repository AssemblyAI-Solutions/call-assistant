/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      colors: {
        'custom-blue': '#1C0644',
        'custom-off-blue': '#3C92DC',
        'custom-black': '#000000',
        'custom-white': '#ffffff',
      },
      fontFamily: {
        'sans': ['Roboto', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        // ... other font families
      },
    },
  },
  plugins: [],
}
