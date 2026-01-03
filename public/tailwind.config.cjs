/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: "class",
    content: ["./index.html", "./*.svelte", "./*.js"],
    theme: {
      extend: {
        fontFamily: {
          sans: ["Merriweather", "serif"],
          serif: ["Merriweather", "serif"]
        },
        boxShadow: {
          soft: "0 12px 40px rgba(0,0,0,0.08)",
          softDark: "0 16px 50px rgba(0,0,0,0.45)"
        }
      }
    },
    plugins: []
  };
  