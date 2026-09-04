"""
FastAPI Application - REST API for Outreach Architect
"""

import contextlib
import os
import secrets
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Base, Lead, OutreachCampaign, OutreachStatus


def _get_orchestrator(db):
    """
    Imported on first use, not at module scope.

    orchestrator -> kimi_agent -> openai, so importing this module previously
    required the whole LLM stack to be installed before the service could serve
    even /health.
    """
    from orchestrator import OutreachOrchestrator

    return OutreachOrchestrator(db)


# Database setup.
#
# create_all() previously ran at module import, so importing this module opened
# a database connection and created tables as a side effect. Nothing could be
# imported without a live database, and the schema was created outside Alembic
# even though Alembic is a declared dependency. It runs in the lifespan handler
# now, and only for SQLite; Postgres deployments should use migrations.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite schema ensured")
    else:
        logger.info("Non-SQLite database: run Alembic migrations before serving")
    yield
    engine.dispose()


app = FastAPI(
    title="Personalized Outreach Architect",
    # The previous description claimed "15-20% response rates". No measurement
    # in this repository supports that, and it was being served in the OpenAPI
    # document as though it were a property of the software.
    description="Research-assisted personalisation for cold outreach campaigns.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    # Was allow_origins=["*"] with allow_credentials=True, a combination
    # browsers reject outright.
    allow_origins=settings.cors_allow_origins
    or ([] if settings.is_production else ["http://localhost:5173", "http://localhost:3000"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# ---- Authentication --------------------------------------------------------
# Every endpoint was previously unauthenticated, including
# POST /campaigns/{id}/send, which delivers email through the configured
# SendGrid account. Anyone who could reach the port could send mail as you.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Depends(_api_key_header)) -> str:
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return api_key


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models for API
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: str | None = None
    job_title: str | None = None
    linkedin_url: HttpUrl | None = None
    location: str | None = None
    company_website: HttpUrl | None = None
    source: str | None = "manual"
    tags: list[str] | None = None


class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    company: str | None
    job_title: str | None
    linkedin_url: str | None
    personalization_score: float
    relevance_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignRequest(BaseModel):
    lead_ids: list[int]
    company_context: str
    value_proposition: str
    auto_send: bool = False
    generate_ab_variants: bool = False


class CampaignResponse(BaseModel):
    id: int
    lead_id: int
    subject_line: str
    email_body: str
    personalization_elements: list[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# API Endpoints


# ---- Operational endpoints -------------------------------------------------
@app.get("/health", tags=["ops"])
async def health() -> dict[str, Any]:
    """Liveness. Deliberately touches no dependency."""
    return {"status": "healthy", "environment": settings.environment, "version": app.version}


@app.get("/ready", tags=["ops"])
async def ready():
    """Readiness: report every dependency needed to serve real traffic."""
    from fastapi.responses import JSONResponse
    from sqlalchemy import text

    checks: dict[str, Any] = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"ok": True, "required": True}
    except Exception as exc:
        logger.error(f"database not ready: {exc}")
        checks["database"] = {"ok": False, "required": True}

    checks["llm_credentials"] = {
        "ok": any(
            (
                settings.kimi_api_key,
                settings.deepseek_api_key,
                settings.anthropic_api_key,
                settings.openai_api_key,
            )
        ),
        "required": False,
    }
    checks["api_key"] = {
        "ok": not (settings.is_production and settings.has_insecure_api_key),
        "required": True,
    }
    checks["email_sending"] = {
        "ok": True,
        "enabled": settings.email_sending_enabled,
        "required": False,
    }

    is_ready = all(c["ok"] for c in checks.values() if c["required"])
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"ready": is_ready, "checks": checks},
    )


@app.get("/")
async def root():
    """Health check"""
    return {"status": "healthy", "service": "Personalized Outreach Architect", "version": "1.0.0"}


@app.post("/leads", response_model=LeadResponse, dependencies=[Depends(require_api_key)])
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """
    Create a new lead

    This creates a lead record but doesn't process it yet.
    Use POST /campaigns to generate personalized outreach.
    """

    # Check if email already exists
    existing = db.query(Lead).filter(Lead.email == lead.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lead with this email already exists")

    db_lead = Lead(
        name=lead.name,
        email=lead.email,
        company=lead.company,
        job_title=lead.job_title,
        linkedin_url=str(lead.linkedin_url) if lead.linkedin_url else None,
        location=lead.location,
        company_website=str(lead.company_website) if lead.company_website else None,
        source=lead.source,
        tags=lead.tags or [],
    )

    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    logger.info(f"Created lead: {db_lead.name} ({db_lead.email})")

    return db_lead


@app.get("/leads", response_model=list[LeadResponse], dependencies=[Depends(require_api_key)])
async def list_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all leads"""
    leads = db.query(Lead).offset(skip).limit(limit).all()
    return leads


@app.get("/leads/{lead_id}", response_model=LeadResponse, dependencies=[Depends(require_api_key)])
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get specific lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.post("/campaigns", dependencies=[Depends(require_api_key)])
async def create_campaign(
    request: CampaignRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Create personalized outreach campaigns for leads

    This is the main endpoint that:
    1. Enriches lead data (LinkedIn + Company Intel)
    2. Analyzes with Kimi AI
    3. Generates hyper-personalized emails
    4. Optionally sends them (if auto_send=True)

    Processing happens in background for large batches.
    """

    # Validate leads exist
    leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    if len(leads) != len(request.lead_ids):
        raise HTTPException(status_code=404, detail="Some lead IDs not found")

    # Create orchestrator
    orchestrator = _get_orchestrator(db)

    # For small batches, process synchronously
    if len(request.lead_ids) <= 5:
        logger.info(f"Processing {len(request.lead_ids)} leads synchronously")

        results = await orchestrator.batch_process_leads(
            lead_ids=request.lead_ids,
            company_context=request.company_context,
            value_proposition=request.value_proposition,
            auto_send=request.auto_send,
        )

        return {
            "status": "completed",
            "results": results["results"],
            "statistics": results["statistics"],
        }

    # For large batches, process in background
    else:
        logger.info(f"Processing {len(request.lead_ids)} leads in background")

        background_tasks.add_task(
            orchestrator.batch_process_leads,
            lead_ids=request.lead_ids,
            company_context=request.company_context,
            value_proposition=request.value_proposition,
            auto_send=request.auto_send,
        )

        return {
            "status": "processing",
            "message": f"Processing {len(request.lead_ids)} leads in background",
            "lead_ids": request.lead_ids,
        }


@app.get(
    "/campaigns", response_model=list[CampaignResponse], dependencies=[Depends(require_api_key)]
)
async def list_campaigns(
    status: OutreachStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all campaigns with optional status filter"""

    query = db.query(OutreachCampaign)

    if status:
        query = query.filter(OutreachCampaign.status == status)

    campaigns = query.offset(skip).limit(limit).all()
    return campaigns


@app.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get specific campaign"""
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.post("/campaigns/{campaign_id}/send", dependencies=[Depends(require_api_key)])
async def send_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Manually send a campaign email

    Use this to send emails that were generated but not auto-sent
    """

    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status == OutreachStatus.SENT:
        raise HTTPException(status_code=400, detail="Campaign already sent")

    orchestrator = _get_orchestrator(db)
    result = await orchestrator._send_email(campaign)

    return {"status": "sent", "campaign_id": campaign_id, "sent_at": result["sent_at"]}


@app.get("/analytics/stats", dependencies=[Depends(require_api_key)])
async def get_analytics(db: Session = Depends(get_db)):
    """
    Get overall analytics and performance metrics
    """

    total_leads = db.query(Lead).count()
    total_campaigns = db.query(OutreachCampaign).count()

    sent_campaigns = (
        db.query(OutreachCampaign).filter(OutreachCampaign.status == OutreachStatus.SENT).count()
    )

    replied_campaigns = (
        db.query(OutreachCampaign).filter(OutreachCampaign.reply_received.is_(True)).count()
    )

    response_rate = (replied_campaigns / sent_campaigns * 100) if sent_campaigns > 0 else 0

    return {
        "total_leads": total_leads,
        "total_campaigns": total_campaigns,
        "sent_campaigns": sent_campaigns,
        "replied_campaigns": replied_campaigns,
        "response_rate": round(response_rate, 2),
        "target_response_rate": "15-20%",
    }


@app.post("/test/kimi", dependencies=[Depends(require_api_key)])
async def test_kimi_connection():
    """Test Kimi AI connection"""

    from kimi_agent import kimi_agent

    try:
        # Simple test
        test_data = {
            "name": "Test User",
            "company": "Test Company",
            "job_title": "Test Role",
            "linkedin_profile": {},
            "recent_activity": [],
        }

        result = await kimi_agent.analyze_lead_profile(test_data)

        return {
            "status": "success",
            "message": "Kimi AI connection successful",
            "test_result": result,
        }

    except Exception as e:
        # Do not echo the provider's exception text back to the caller: it can
        # carry endpoint URLs and key fragments.
        logger.error(f"LLM connectivity check failed: {e}")
        raise HTTPException(
            status_code=503, detail="LLM provider is not reachable. Check the server logs."
        ) from e


if __name__ == "__main__":
    import uvicorn

    # Binding all interfaces is correct inside a container and wrong on a
    # laptop; default to loopback and let deployment opt in.
    uvicorn.run(
        "main:app",
        host=os.environ.get("BIND_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
