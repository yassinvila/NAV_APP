# NAV_APP

Natural-language navigation app with a FastAPI backend and a React + Vite frontend.

## What We Built

### Backend
- FastAPI app with `POST /navigation/route` for navigation requests.
- Beta access endpoint with a PIN gate.
- Username/password account creation and login endpoints.
- PostgreSQL-backed saved location lookup for `home` and `work`.
- Mapbox Geocoding and Directions integration handled only in the backend.
- Shared root `.env` loading for configuration.
- Dockerfile and backend startup instructions.

### Frontend
- Full-page Mapbox GL JS map display.
- Browser geolocation for the user’s current location.
- User marker, destination marker, and route line drawing.
- Search box for natural-language navigation commands.
- Route info panel for distance and duration.
- Debug panel for parsed command, destination, and route payload.
- Beta PIN gate shown before any login.
- Username/password login and account creation flow with no email field.
- Shared root `.env` loading for frontend configuration.

## What We Did Not Build Yet

- Persistent login sessions or JWT auth.
- Password reset or account recovery.
- Admin dashboard for managing beta access or users.
- Full production hardening for auth, secrets, and rate limiting.
- Seed scripts or migrations for PostgreSQL.
- Frontend styling polish beyond a functional beta UI.
- End-to-end automated tests.
- A dedicated model-serving microservice; the backend now loads the T5 parser directly from the Hugging Face repo or local path.

## Repository Layout

- `backend/` contains the FastAPI API, database models, services, and backend README.
- `frontend/` contains the React app, Mapbox UI, and frontend README.
- `.env` at the repo root is the shared configuration file for both apps.

## Current Flow

1. User opens the frontend.
2. Beta PIN gate appears first.
3. User logs in or creates an account with username and password.
4. The app asks for browser location access.
5. User enters a navigation command.
6. Frontend sends the command and current coordinates to the backend.
7. Backend parses the command, resolves the destination, generates the route, and returns route data.
8. Frontend renders the route and destination on the map.

## Quick Start

1. Fill in the root `.env` file.
2. Start PostgreSQL.
3. Run the backend from `backend/`.
4. Run the frontend from `frontend/`.

For more detail, see:
- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
