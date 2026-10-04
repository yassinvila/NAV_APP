# Navigation Backend

Minimal FastAPI backend for the natural-language navigation workflow.

## What it does

- Accepts a user command and current location
- Parses the command with a T5-based model adapter
- Resolves home/work locations from PostgreSQL
- Uses Mapbox Geocoding for places and categories
- Uses Mapbox Directions to build a route
- Returns parsed command data, destination details, and route geometry

## Start Up

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a single `.env` file at the repository root and fill in your values.
4. Start PostgreSQL and make sure `DATABASE_URL` points to it.
5. Run the API from the `backend` folder:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Example Request

```json
{
  "user_id": 1,
  "text": "find nearest cafe",
  "current_location": {
    "latitude": 40.6782,
    "longitude": -73.9442
  }
}
```

## Example Endpoint

- `POST /navigation/route`
- `GET /health`
- `POST /models/warmup?model_key=T5_NEMO` loads one configured model into the Hugging Face disk cache and the backend process cache. The frontend preloads T5_NEMO when the app opens; T5_CLAUDE is loaded lazily if selected.

Authenticated endpoints use a JWT returned by registration and login. The frontend stores that token for the demo session and sends it with navigation and profile requests. API requests are limited to `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS` per client and endpoint. Outbound Mapbox requests use `REQUEST_TIMEOUT_SECONDS`.

To inspect the Claude checkpoint and run sample generations, use the repository virtual environment from the repository root:

```bash
python backend/scripts/check_claude_model.py
```

The script reports the T5 configuration, shared embedding aliases, and whether sample outputs are valid JSON. It reads `HF_TOKEN_TWO` or `HF_TOKEN` from the environment when private model access is required.

## Notes

- Set `MODEL_NAME_OR_PATH` to the Hugging Face repo id or local path for the T5 parser.
- If your fine-tune expects a task prefix, set `MODEL_INPUT_PREFIX` in the root `.env`.
- The backend creates its SQLAlchemy tables on startup for the minimal setup.
- `CORS_ALLOW_ORIGINS=*` works for local frontend development.
- Set `BETA_ACCESS_PIN` in the root `.env` to control beta entry.
- Account endpoints are `POST /auth/beta-pin`, `POST /auth/register`, and `POST /auth/login`.
- Set `JWT_SECRET` to a private value for the environment running the API.
