from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import chat, drawing, estimate
from app.core.config import ALLOWED_HOSTS, ALLOWED_ORIGINS
from app.db.session import Base, engine
import app.models  # Registers SQLAlchemy mappings before create_all.

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Precast Suspended Slab Estimator", version="1.0.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
app.include_router(estimate.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(drawing.router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="app/static", html=True), name="dashboard")
