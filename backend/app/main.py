"""Main FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.api import api_router
from backend.app.storage.db import InvestigationStore
from backend.app.agent.orchestrator import InvestigationOrchestrator
from backend.app.observability.simulated_data import ActiveScenarioManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed initial flagship investigation if store is empty
    existing = InvestigationStore.list_all()
    if not existing:
        logger.info("Seeding initial flagship multi-source investigation demo...")
        ActiveScenarioManager.set_scenario("multi_source")
        orch = InvestigationOrchestrator()
        seed_state = orch.run_full_investigation(
            incident="The checkout service suddenly has a high 5xx error rate, probe failures, and restarts.",
            namespace="default",
            max_steps=8
        )
        InvestigationStore.save(seed_state)
        logger.info(f"Seeded demo investigation {seed_state.id} with confidence {seed_state.confidence}%.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Advanced Autonomous AI Agent for Kubernetes Root-Cause Analysis and Multi-Source Observability Correlation.",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "version": settings.VERSION,
        "security_sandbox": settings.ENABLE_SECURITY_SANDBOX,
        "llm_provider": settings.LLM_PROVIDER
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
