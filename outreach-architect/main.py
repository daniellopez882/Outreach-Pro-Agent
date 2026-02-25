"""
FastAPI Application - REST API for Outreach Architect
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from config import settings
from models import Base, Lead, OutreachCampaign, OutreachStatus
from orchestrator import OutreachOrchestrator

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Personalized Outreach Architect",
    description="Hyper-personalized cold outreach with 15-20% response rates",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    company: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    company_website: Optional[HttpUrl] = None
    source: Optional[str] = "manual"
    tags: Optional[List[str]] = None


class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    company: Optional[str]
    job_title: Optional[str]
    linkedin_url: Optional[str]
    personalization_score: float
    relevance_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class CampaignRequest(BaseModel):
    lead_ids: List[int]
    company_context: str
    value_proposition: str
    auto_send: bool = False
    generate_ab_variants: bool = False


class CampaignResponse(BaseModel):
    id: int
    lead_id: int
    subject_line: str
    email_body: str
    personalization_elements: List[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# API Endpoints

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Personalized Outreach Architect",
        "version": "1.0.0"
    }


@app.post("/leads", response_model=LeadResponse)
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
        tags=lead.tags or []
    )
    
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    logger.info(f"Created lead: {db_lead.name} ({db_lead.email})")
    
    return db_lead


@app.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all leads"""
    leads = db.query(Lead).offset(skip).limit(limit).all()
    return leads


@app.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get specific lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.post("/campaigns")
async def create_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
    orchestrator = OutreachOrchestrator(db)
    
    # For small batches, process synchronously
    if len(request.lead_ids) <= 5:
        logger.info(f"Processing {len(request.lead_ids)} leads synchronously")
        
        results = await orchestrator.batch_process_leads(
            lead_ids=request.lead_ids,
            company_context=request.company_context,
            value_proposition=request.value_proposition,
            auto_send=request.auto_send
        )
        
        return {
            "status": "completed",
            "results": results['results'],
            "statistics": results['statistics']
        }
    
    # For large batches, process in background
    else:
        logger.info(f"Processing {len(request.lead_ids)} leads in background")
        
        background_tasks.add_task(
            orchestrator.batch_process_leads,
            lead_ids=request.lead_ids,
            company_context=request.company_context,
            value_proposition=request.value_proposition,
            auto_send=request.auto_send
        )
        
        return {
            "status": "processing",
            "message": f"Processing {len(request.lead_ids)} leads in background",
            "lead_ids": request.lead_ids
        }


@app.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[OutreachStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all campaigns with optional status filter"""
    
    query = db.query(OutreachCampaign)
    
    if status:
        query = query.filter(OutreachCampaign.status == status)
    
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns


@app.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get specific campaign"""
    campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.post("/campaigns/{campaign_id}/send")
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
    
    orchestrator = OutreachOrchestrator(db)
    result = await orchestrator._send_email(campaign)
    
    return {
        "status": "sent",
        "campaign_id": campaign_id,
        "sent_at": result['sent_at']
    }


@app.get("/analytics/stats")
async def get_analytics(db: Session = Depends(get_db)):
    """
    Get overall analytics and performance metrics
    """
    
    total_leads = db.query(Lead).count()
    total_campaigns = db.query(OutreachCampaign).count()
    
    sent_campaigns = db.query(OutreachCampaign).filter(
        OutreachCampaign.status == OutreachStatus.SENT
    ).count()
    
    replied_campaigns = db.query(OutreachCampaign).filter(
        OutreachCampaign.reply_received == True
    ).count()
    
    response_rate = (replied_campaigns / sent_campaigns * 100) if sent_campaigns > 0 else 0
    
    return {
        "total_leads": total_leads,
        "total_campaigns": total_campaigns,
        "sent_campaigns": sent_campaigns,
        "replied_campaigns": replied_campaigns,
        "response_rate": round(response_rate, 2),
        "target_response_rate": "15-20%"
    }


@app.post("/test/kimi")
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
            "recent_activity": []
        }
        
        result = await kimi_agent.analyze_lead_profile(test_data)
        
        return {
            "status": "success",
            "message": "Kimi AI connection successful",
            "test_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kimi AI connection failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
