/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paytm: {
          blue: "#00BAF2",
          dark: "#002E6E",
          navy: "#0F1E36",
          accent: "#00B9F5",
          gold: "#F59E0B",
          surface: "#F4F8FA",
          card: "#FFFFFF",
          text: "#1E293B",
          muted: "#64748B"
        }
      },
      keyframes: {
        pulseRing: {
          '0%': { transform: 'scale(0.95)', opacity: '0.8' },
          '50%': { transform: 'scale(1.15)', opacity: '0.3' },
          '100%': { transform: 'scale(0.95)', opacity: '0.8' }
        },
        wave: {
          '0%, 100%': { transform: 'scaleY(0.4)' },
          '50%': { transform: 'scaleY(1.0)' }
        }
      },
      animation: {
        'pulse-ring': 'pulseRing 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'wave-bar': 'wave 1s ease-in-out infinite'
      }
    },
  },
  plugins: [],
}
