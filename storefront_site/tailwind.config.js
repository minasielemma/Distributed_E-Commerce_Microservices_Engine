/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        amazon: {
          header: {
            primary: '#131921',
            secondary: '#232F3E',
          },
          canvas: '#EAEDED',
          surface: '#FFFFFF',
          orange: '#FF9900',
          cta: {
            primary: '#FFD814',
            primaryHover: '#F7CA00',
            secondary: '#FFA41C',
            secondaryHover: '#FA8900'
          },
          deal: {
            red: '#CC0C39',
          },
          price: {
            red: '#B12704',
          },
          stock: {
            green: '#007600',
          },
          link: {
            teal: '#007185',
          },
          prime: {
            blue: '#00A8E1',
          },
          text: {
            primary: '#0F1111',
            secondary: '#565959',
          },
          border: {
            card: '#D5D9D9',
          }
        }
      },
      fontFamily: {
        sans: ['"Amazon Ember"', 'Arial', 'sans-serif'],
      },
      zIndex: {
        '0': '0',
        '10': '10',
        '20': '20',
        '30': '30',
        '40': '40',
        '50': '50',
        '100': '100',
      }
    },
  },
  plugins: [],
}
