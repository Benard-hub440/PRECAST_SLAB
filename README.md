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

## Local AI drawing takeoff

The drawing feature never sends drawings to a hosted AI provider. It uses a
vision-capable [Ollama](https://ollama.com/) model running on the same machine.
After installing Ollama, pull a vision model and start the application:

```bash
ollama pull qwen2.5vl:7b
uvicorn app.main:app --reload
```

Upload a dimensioned PDF of an architectural or structural plan in **Read a
drawing**. The server renders up to eight PDF sheets in memory for the local
vision model; the uploaded drawing is not saved. The model returns explicitly labelled room dimensions;
the existing, deterministic calculator then produces a T-beam, 1 m slab-panel,
and 3 m wall-panel estimate for each room and project totals. Wall panels are
based on each extracted room perimeter, so openings and shared walls must be
checked against the issued drawings before ordering. The screen shows the
extracted dimensions, confidence, and source-label evidence.

Set `OLLAMA_URL` to use a different local Ollama address and
`OLLAMA_VISION_MODEL` to select another locally installed vision model.

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
