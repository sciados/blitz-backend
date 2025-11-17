<<<<<<< HEAD
# blitz-frontend
=======
# blitz-frontend

Frontend for Blitz (Next.js 14 + Tailwind + React Query).

## Setup

1) Install
   npm install

2) Configure env
   cp .env.local.example .env.local

   # Set NEXT_PUBLIC_API_BASE_URL to your FastAPI base URL

3) Run
   npm run dev

   # open <http://localhost:3000>

## Deploy (Vercel)

- Set NEXT_PUBLIC_API_BASE_URL in Vercel Project Settings -> Environment Variables.
- Connect repo and deploy.

Next steps

Push these files to your blitz-frontend repo.
In the backend, confirm all route prefixes use /api to match the frontend calls.
Set CORS to allow <http://localhost:3000> and your Vercel domains.
Share any schema decisions (content/intelligence shape), and I’ll adjust the frontend types and forms accordingly.
Want me to add a sidebar shell and navigation? Say “add shell,” and I’ll provide a simple app layout with a sidebar for all sections.
>>>>>>> 12f8744 (chore: initial Next.js scaffold)
