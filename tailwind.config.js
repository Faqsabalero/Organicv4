/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./core/templates/**/*.html",
    "./core/static/**/*.js",
  ],
  theme: {
    extend: {
      animation: {
        'gradient': 'gradient 15s ease infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        },
        shimmer: {
          '0%': {
            'background-position': '-200% center',
          },
          '100%': {
            'background-position': '200% center',
          },
        },
        float: {
          '0%, 100%': {
            transform: 'translateY(0)',
          },
          '50%': {
            transform: 'translateY(-20px)',
          },
        },
      },
    },
  },
  plugins: [],
}
