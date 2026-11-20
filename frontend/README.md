# AuthForge Frontend

React + TypeScript + Vite console for the AuthForge FastAPI backend.

## Stack

- React 19 + TypeScript
- Vite 8
- React Router
- TanStack Query
- Tailwind CSS v4 + shadcn/ui
- Axios with a single-flight refresh-token interceptor

## Setup

```bash
npm install
cp .env.example .env   # optionally point VITE_API_URL at the backend
npm run dev
```

The app runs on http://localhost:5173 and calls the backend at
`http://localhost:8000` by default. To use a different backend:

```env
VITE_API_URL=http://localhost:8000
```

## Backend configuration

The backend must allow the frontend origin. In the repository root `.env`:

```env
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

Verification and password-reset emails now link to the SPA routes
`/verify-email?token=...` and `/reset-password?token=...`.

## Auth model

- The access token is kept in memory only.
- The refresh token is stored in `localStorage` under `authforge.refresh_token`.
- A single refresh request is shared by concurrent 401 responses.
- On refresh failure the session is cleared and protected routes redirect to `/login`.

## Scripts

```bash
npm run dev      # development server
npm run build    # type-check and production build
npm run preview  # preview the production build
npm run lint     # oxlint
```

## Routes

| Route | Access | Purpose |
|---|---|---|
| `/login`, `/register` | public | Sign in / create account |
| `/forgot-password`, `/reset-password` | public | Password reset flow |
| `/verify-email`, `/resend-verification` | public | Email verification |
| `/two-factor` | public | TOTP challenge after login |
| `/dashboard` | authenticated | Account overview |
| `/security` | authenticated | Password + TOTP management |
| `/api-keys` | authenticated | Service account keys |
| `/admin/users` | Admin | User search, role and status management |
| `/admin/audit` | Admin | Audit log with filters |
