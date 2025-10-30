/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: 'var(--accent-primary)',
                'accent-primary': 'var(--accent-primary)',
                'accent-secondary': 'var(--accent-secondary)',

                'bg-primary': 'var(--bg-primary)',
                'bg-secondary': 'var(--bg-secondary)',

                'card-bg': 'var(--card-bg)',
                'card-border': 'var(--card-border)',

                'text-primary': 'var(--text-primary)',
                'text-secondary': 'var(--text-secondary)',

                'hover-bg': 'var(--hover-bg)',
                'border-color': 'var(--border-color)',
            },
            boxShadow: {
                'card-sm': '0 1px 2px rgba(0,0,0,0.06)',
            },
        },
    },
    // If you use arbitrary bg-[var(--...)] classes at runtime, you can safelist them:
    // safelist: [
    //   'bg-[var(--bg-primary)]',
    //   'bg-[var(--bg-secondary)]',
    //   'bg-[var(--card-bg)]',
    // ],
    plugins: [],
};