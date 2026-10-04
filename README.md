# NAV_APP

Natural-language navigation demo with a FastAPI backend, a React/Vite frontend, Mapbox routing, and T5 command parsing.

## Repository layout

- `backend/` - FastAPI API, model service, database models, tests, and model tools.
- `frontend/` - React/Vite map interface.
- `.env.example` - safe local configuration template.
- `.env` - your local secrets and settings; never commit this file.

## Run locally with Git Bash

### 1. Create the environment

From the repository root:

```bash
python -m venv venv
source venv/Scripts/activate
cp .env.example .env
```

Edit `.env` and provide a Mapbox token. For local development, SQLite is the default database. Use PostgreSQL by replacing `DATABASE_URL` when needed.

### 2. Install backend dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

### 3. Start the backend

Run this from the `backend` directory:

```bash
python -m uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Verify it with:

```bash
curl http://127.0.0.1:8000/health
```

### 4. Start the frontend

Open a second Git Bash window:

```bash
cd /c/Users/YASS/OneDrive/Desktop/NAV_APP/frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Models

The default template points to the quantized CPU repositories:

```env
T5_NEMO=yassinvila/nav_model_int8
T5_CLAUDE=yassinvila/nav_model_claude_int8
```

The backend downloads a selected model on its first navigation request. Public repositories do not require a token; set `HF_TOKEN` or `HF_TOKEN_TWO` only for private repositories. Model artifacts are not stored in Git.

To create a quantized model locally:

```bash
python backend/scripts/quantize_model.py \
  --model yassinvila/nav_model \
  --output backend/models/nav_model_int8
```

To upload a generated model:

```bash
python backend/scripts/upload_model.py \
  --folder backend/models/nav_model_int8 \
  --repo YOUR_HF_USERNAME/nav_model_int8
```

## Useful commands

Backend tests:

```bash
cd backend
python -m pytest -q
```

Frontend lint and build:

```bash
cd frontend
npm run lint
npm run build
```

See [backend/README.md](backend/README.md) for API behavior, authentication, rate limits, and model tooling.
