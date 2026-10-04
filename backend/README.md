# Navigation Backend

Minimal FastAPI backend for the natural-language navigation workflow.

## What it does

- Accepts a user command and current location
- Parses the command with a T5-based model adapter
- Resolves home/work locations from PostgreSQL
- Uses Mapbox Geocoding for places and categories
- Uses Mapbox Directions to build a route
- Returns parsed command data, destination details, and route geometry

## Local startup

From Git Bash at the repository root:

```bash
python -m venv venv
source venv/Scripts/activate
cp .env.example .env
cd backend
python -m pip install -r requirements.txt
```

Start the API from the `backend` directory:

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Configuration

Copy `.env.example` to `.env` and set at least `MAPBOX_ACCESS_TOKEN`, `BETA_ACCESS_PIN`, and `JWT_SECRET`. SQLite is used by default for local development. Set `DATABASE_URL` to PostgreSQL for a deployed or shared environment.

The default model settings use the public quantized repositories:

```env
T5_NEMO=yassinvila/nav_model_int8
T5_CLAUDE=yassinvila/nav_model_claude_int8
```

Models are downloaded lazily on the first request that selects them. Keep Hugging Face tokens in `.env` or the deployment provider's secret settings; never commit them.

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
- `POST /models/warmup?model_key=T5_NEMO` can manually load one configured model into the backend process cache. The frontend does not call this endpoint automatically; models load on demand during navigation.

Authenticated endpoints use a JWT returned by registration and login. The frontend stores that token for the demo session and sends it with navigation and profile requests. API requests are limited to `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS` per client and endpoint. Outbound Mapbox requests use `REQUEST_TIMEOUT_SECONDS`.

To inspect the Claude checkpoint and run sample generations, use the repository virtual environment from the repository root:

```bash
python backend/scripts/check_claude_model.py
```

The script reports the T5 configuration, shared embedding aliases, and whether sample outputs are valid JSON. It reads `HF_TOKEN_TWO` or `HF_TOKEN` from the environment when private model access is required.

To create a CPU-only dynamic INT8 checkpoint for a trusted local model:

```bash
python backend/scripts/quantize_model.py \
  --model yassinvila/nav_model_claude \
  --output backend/models/nav_model_claude_int8
```

Point `T5_CLAUDE` at the generated directory to use its `quantized_model.pt` file. The generated model directory is ignored by Git because model artifacts should be stored in model hosting or deployment storage rather than committed to the source repository. Only load checkpoints generated and controlled by you; the loader uses trusted pickle deserialization for this format.

## Notes

- Set `MODEL_NAME_OR_PATH` to the Hugging Face repo id or local path for the T5 parser.
- If your fine-tune expects a task prefix, set `MODEL_INPUT_PREFIX` in the root `.env`.
- The backend creates its SQLAlchemy tables on startup for the minimal setup.
- `CORS_ALLOW_ORIGINS=*` works for local frontend development.
- Set `BETA_ACCESS_PIN` in the root `.env` to control beta entry.
- Account endpoints are `POST /auth/beta-pin`, `POST /auth/register`, and `POST /auth/login`.
- Set `JWT_SECRET` to a private value for the environment running the API.
