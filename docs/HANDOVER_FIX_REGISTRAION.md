# Blitz Auth Fix Handover

## Overview

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL on Railway
- Frontend: Next.js 14 + TypeScript on Vercel
- Focus: Fix 500 on POST /api/auth/register and finalize auth

## Current Status

- Frontend now targets backend correctly.
- Verified request:
  - POST <https://blitzed.up.railway.app/api/auth/register>
- Failure:
  - 500 Internal Server Error
- Root cause (Railway logs):
  - passlib/bcrypt raised “password cannot be longer than 72 bytes”
- Resolution approach:
  - Use passlib bcrypt_sha256 to avoid the 72-byte limit
  - Add password length validation and proper 400 responses
  - Ensure env var NEXT_PUBLIC_API_BASE_URL embedded in frontend

## Files To Update

### 1) Backend: auth.py (complete)

- Provide password hashing
- JWT creation/verification
- User helpers
- FastAPI dependencies (get_current_user, get_current_active_user)

Key changes:

- Use `bcrypt_sha256` in passlib
- Defensive checks and logging

### 2) Backend: requirements.txt

Ensure the following packages are present:

- passlib[bcrypt]>=1.7.4
- bcrypt>=4.1.2
- python-jose[cryptography]>=3.3.0
- fastapi, uvicorn, sqlalchemy, alembic, psycopg[binary], pydantic, starlette, email-validator, python-multipart

### 3) Backend: app/api/auth.py (register route)

Add validation so API returns 400 instead of 500 on invalid input:

- Require 8–128 characters (adjust policy as needed)
- Check for duplicate emails (409)

Return shape on success:

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User",
  "access_token": "<jwt>",
  "token_type": "bearer"
}

Environment Variables
Frontend (Vercel):

NEXT_PUBLIC_API_BASE_URL = https://blitzed.up.railway.app
Set for All Environments (Production, Preview, Development)
Backend (Railway):

DATABASE_URL
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES (e.g., 60)
ALGORITHM = HS256
CORS
Allow origins should include:

https://YOUR-VERCEL-APP.vercel.app
Optionally preview domains or a dynamic check
http://localhost:3000 for local dev
Manual Tests
Health:

GET https://blitzed.up.railway.app/health → 200 OK
Docs:

GET https://blitzed.up.railway.app/docs → check /api/auth/register schema
Register (curl):

bash
Copy
curl -i -X POST https://blitzed.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@example.com","full_name":"Test User","password":"Abcdef12!"}'
Expected:

200/201 with user and token, or
400 with clear detail for validation errors, or
409 if email exists
Frontend Notes
Single axios client (example):

ts
Copy
import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://blitzed.up.railway.app";

export const api = axios.create({
  baseURL,
  withCredentials: false
});
Register call:

ts
Copy
await api.post("/api/auth/register", {
  email,
  full_name,
  password
});
To verify at runtime:

Console should show: “Blitz API baseURL: https://blitzed.up.railway.app”
Network tab should show requests to Railway (not localhost)
Next Session Targets
Deploy backend with updated auth.py and requirements.txt
Add password length checks in register route
Test registration with a normal password and new email
If still failing, capture:
Response JSON (Network tab)
Railway traceback around the request timestamp
Confirm route prefix and response shape consistency across frontend/backend
Open Questions
Do we need dual-hash verification for any pre-existing bcrypt users?
Final minimum/maximum password policy to enforce?
Confirm import paths for get_db, User, and settings in your project structure
Notes About Uploaded Files
appClient.ts and next.config.js were previously unextractable in the tool; these documents can only be used in code execution. Extraction can fail due to encoding/minification. We provided working code examples inline.
