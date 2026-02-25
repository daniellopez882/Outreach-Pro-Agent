"""
Database models for the Outreach Architect
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, 
    Text, Boolean, JSON, ForeignKey, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class OutreachStatus(str, enum.Enum):
    """Status of outreach campaign"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    READY = "ready"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"
    SKIPPED = "skipped"


class Lead(Base):
    """Lead/Prospect information"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    company = Column(String(255))
    job_title = Column(String(255))
    location = Column(String(255))
    
    # LinkedIn Data
    linkedin_url = Column(String(500), unique=True, index=True)
    linkedin_profile_data = Column(JSON)  # Complete profile dump
    recent_posts = Column(JSON)  # Last 5-10 posts
    recent_activity = Column(JSON)  # Likes, comments, shares
    
    # Company Data
    company_website = Column(String(500))
    company_news = Column(JSON)  # Recent news articles
    company_size = Column(String(50))
    company_industry = Column(String(255))
    
    # Enrichment Data
    pain_points = Column(JSON)  # Identified pain points
    interests = Column(JSON)  # Professional interests
    trigger_events = Column(JSON)  # Recent events for outreach
    
    # Personalization Score
    personalization_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    
    # Metadata
    source = Column(String(100))  # Where lead came from
    tags = Column(JSON)  # Custom tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_enriched_at = Column(DateTime)
    
    # Relationships
    outreach_campaigns = relationship("OutreachCampaign", back_populates="lead")


class OutreachCampaign(Base):
    """Outreach campaign for a specific lead"""
    __tablename__ = "outreach_campaigns"
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    
    # Campaign Info
    subject_line = Column(String(500))
    email_body = Column(Text)
    personalization_elements = Column(JSON)  # What was personalized
    
    # Generation Details
    prompt_used = Column(Text)
    model_used = Column(String(100))
    generation_metadata = Column(JSON)
    
    # Status & Tracking
    status = Column(Enum(OutreachStatus), default=OutreachStatus.PENDING)
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)
    
    # Engagement Metrics
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    reply_received = Column(Boolean, default=False)
    reply_content = Column(Text)
    
    # A/B Testing
    variant = Column(String(50))  # A, B, C, etc.
    test_group = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="outreach_campaigns")
    follow_ups = relationship("FollowUp", back_populates="campaign")


class FollowUp(Base):
    """Follow-up emails in a sequence"""
    __tablename__ = "follow_ups"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"), nullable=False)
    
    sequence_number = Column(Integer)  # 1, 2, 3, etc.
    subject_line = Column(String(500))
    email_body = Column(Text)
    
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    status = Column(Enum(OutreachStatus), default=OutreachStatus.PENDING)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("OutreachCampaign", back_populates="follow_ups")


class AnalyticsEvent(Base):
    """Track all events for analytics"""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("outreach_campaigns.id"))
    
    event_type = Column(String(50))  # sent, opened, clicked, replied, etc.
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user_agent = Column(String(500))
    ip_address = Column(String(50))
