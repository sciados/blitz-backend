/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            // Map convenient names to your CSS variables (optional)
            colors: {
                primary: 'var(--accent-primary)',
                'bg-primary': 'var(--bg-primary)',
                'bg-secondary': 'var(--bg-secondary)',
                'card-bg': 'var(--card-bg)',
                'text-primary': 'var(--text-primary)',
                'text-secondary': 'var(--text-secondary)',
            },
            boxShadow: {
                'card-sm': '0 1px 2px rgba(0,0,0,0.06)',
            },
        },
    },
    // Safelist classes that are generated dynamically or used with CSS variables
    // (uncomment and add entries if you use arbitrary classes that Tailwind can't statically detect)
    // safelist: [
    //   'bg-[var(--card-bg)]',
    //   'text-[var(--text-primary)]',
    //   'text-[var(--text-secondary)]',
    // ],
    plugins: [],
};