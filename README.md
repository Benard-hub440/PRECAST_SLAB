# Precast Suspended Slab Material Estimator

A FastAPI and SQLite application for estimating inverted T-beams, 1 m slab
panels, 3 m wall panels, and screed fiber from room dimensions or architectural
drawings.

## Local deployment

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Start the application: `uvicorn app.main:app --reload`
4. Open `http://127.0.0.1:8000`.

The SQLite database is created at `precast_estimator.db` by default. Set
`DATABASE_URL` for another SQLAlchemy-compatible database (for example,
PostgreSQL) in deployment.

## Deployment

Copy `.env.example` to `.env` and set `ALLOWED_HOSTS` to the application's
public host name. Keep `ALLOWED_ORIGINS` empty when the dashboard and API share
one domain; otherwise list only the trusted dashboard origins. Use a managed
database rather than the local SQLite file for a multi-instance deployment.

## Multimodal drawing takeoff

The drawing feature accepts a multimodal model through either local
[Ollama](https://ollama.com/) (the default) or an OpenAI-compatible
chat-completions endpoint. For the local, private setup, pull your selected
vision model and place its name in your untracked `.env` file:

```bash
ollama pull <your-multimodal-model>
uvicorn app.main:app --reload
```

Upload a dimensioned PDF of an architectural or structural plan in **Read a
drawing**. The server renders up to eight PDF sheets in memory for the
configured vision model; the uploaded drawing is not saved. The model returns explicitly labelled room dimensions;
the existing, deterministic calculator then produces a T-beam, 1 m slab-panel,
and 3 m wall-panel estimate for each room and project totals. Wall panels are
based on each extracted room perimeter, so openings and shared walls must be
checked against the issued drawings before ordering. The screen shows the
extracted dimensions, confidence, and source-label evidence.

Set `VISION_PROVIDER=ollama`, `VISION_API_URL`, and `VISION_MODEL` for any
locally installed Ollama vision model. For a hosted or self-hosted
OpenAI-compatible endpoint, set `VISION_PROVIDER=openai_compatible`, point
`VISION_API_URL` at its chat-completions endpoint, and set `VISION_API_KEY`
and `VISION_MODEL`. See `.env.example`.

## Layout

```
app/
  api/routes/       # Versioned HTTP endpoints
  core/             # Settings
  db/               # SQLAlchemy setup
  models/           # Persistence entities
  schemas/          # Pydantic request/response contracts
  services/         # Calculation and chat domain services
  static/           # Dashboard assets
  main.py           # Application factory
tests/              # Calculation tests
```

## Roadmap seams

- `Project`, `Room`, and `Estimate` already model one-to-many project rooms.
- Put rate tables and quotation generation beside `services/` and expose them
  through a new versioned router; estimates deliberately contain quantities only.
- Add a cutting-stock solver that consumes `Estimate.total_beam_linear_meters`
  and room span data without altering the takeoff calculator.
