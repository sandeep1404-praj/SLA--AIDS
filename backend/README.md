# ContentFlow AI — Backend

FastAPI API for articles, content calendars, and Gemini-powered post generation. Uses MongoDB for storage.

## Prerequisites

- **Python 3.11+** (3.12 recommended)
- **MongoDB** — local instance or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) connection string
- **Google Gemini API key** — from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup

### 1. Open the backend folder

```powershell
cd path\to\your\project\backend
```

### 2. Create a virtual environment (recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run once (current user):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

On **macOS / Linux**:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and edit it:

```powershell
copy .env.example .env
```

Set these in **`.env`**:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Gemini API key (required for AI generation) |
| `GEMINI_API_KEYS` | Optional comma-separated fallback keys. A quota or authentication failure switches to the next key. Keep real keys only in local `.env` or a secret manager. |
| `GEMINI_API_KEY_2` ... `GEMINI_API_KEY_9` | Optional individually configured fallback keys. Use these when comma-separated values are inconvenient. |
| `GEMINI_MODEL` | Model id, e.g. `gemini-2.0-flash` |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DATABASE` | Database name (default: `contentflow_ai`) |
| `JWT_SECRET` | Long random string for signing auth tokens |
| `FRONTEND_URL` | Frontend origin for CORS (default: `http://localhost:5173`) |
| `BACKEND_URL` | Backend URL (default: `http://localhost:8000`) |

Example MongoDB Atlas URI shape:

```text
mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

## Run the server

From the **`backend`** directory (with the virtual environment activated):

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **API base:** http://localhost:8000  
- **Health check:** http://localhost:8000/health  
- **Interactive docs:** http://localhost:8000/docs  

The frontend expects the API at `http://localhost:8000` unless you set `VITE_API_BASE_URL` in the frontend `.env`.

### Run without `--reload` (production-style)

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Verify it works

1. Start the server (see above).
2. Open http://localhost:8000/health — you should see `{"status":"healthy"}`.
3. On startup, the console should show `[OK] Connected to MongoDB: ...` if MongoDB is configured correctly.
4. If `GEMINI_API_KEY` is missing, you will see a warning; calendar generation will fail until the key is set.

## Run tests

From **`backend`** with dependencies installed:

```powershell
pytest tests/ -q
```

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `ModuleNotFoundError` | Activate `.venv` and run `pip install -r requirements.txt` |
| `ImportError: cannot import name 'ArgsKwargs'` | Reinstall dependencies with `pip install --force-reinstall -r requirements.txt`; ensure the virtual environment's Python version matches its installed wheels |
| MongoDB connection error | `MONGODB_URI`, network access in Atlas, IP allowlist |
| `429 RESOURCE_EXHAUSTED` | This is a Gemini project/model quota limit, not an application bug. Wait for the quota reset, enable billing, use a model with available quota, or configure a different API key/project. The backend does not retry exhausted quota responses. |
| `validation error for GeneratedPost visual_suggestion` | The backend normalizes list/object values returned by Gemini into text before validating the post. Restart the backend after updating dependencies or code. |
| Calendar generation fails | Valid `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.0-flash`, backend logs |
| CORS errors from frontend | `FRONTEND_URL` matches your Vite dev URL (usually port 5173) |

## Project layout

```text
backend/
  app/
    main.py          # FastAPI entry point
    api/routes/      # HTTP routes
    services/        # Gemini, calendar pipeline, exports
    db/              # MongoDB connection
  requirements.txt
  .env.example
  .env               # local secrets (do not commit)
```
