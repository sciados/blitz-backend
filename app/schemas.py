# app/schemas.py
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class ContentType(str, Enum):
    ARTICLE = "article"
    EMAIL = "email"
    VIDEO_SCRIPT = "video_script"
    SOCIAL_POST = "social_post"
    LANDING_PAGE = "landing_page"
    AD_COPY = "ad_copy"

class MarketingAngle(str, Enum):
    PROBLEM_SOLUTION = "problem_solution"
    TRANSFORMATION = "transformation"
    SCARCITY = "scarcity"
    AUTHORITY = "authority"
    SOCIAL_PROOF = "social_proof"
    COMPARISON = "comparison"
    STORY = "story"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"

# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# ============================================================================
# CAMPAIGN SCHEMAS
# ============================================================================

class CampaignBase(BaseModel):
    name: str
    product_url: HttpUrl
    affiliate_network: str
    target_audience: Optional[str] = None
    marketing_angles: Optional[List[MarketingAngle]] = []

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[CampaignStatus] = None
    target_audience: Optional[str] = None
    marketing_angles: Optional[List[MarketingAngle]] = None

class CampaignResponse(CampaignBase):
    id: int
    user_id: int
    status: CampaignStatus
    intelligence_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CampaignAnalytics(BaseModel):
    campaign_id: int
    total_content: int
    content_by_type: Dict[str, int]
    compliance_score: float
    last_generated: Optional[datetime]

# ============================================================================
# CONTENT GENERATION SCHEMAS
# ============================================================================

class ContentGenerateRequest(BaseModel):
    campaign_id: int
    content_type: ContentType
    marketing_angle: MarketingAngle
    additional_context: Optional[str] = None
    tone: Optional[str] = "professional"
    length: Optional[str] = "medium"  # short, medium, long

class ContentRefineRequest(BaseModel):
    content_id: int
    refinement_instructions: str

class ContentVariationRequest(BaseModel):
    content_id: int
    num_variations: int = Field(default=3, ge=1, le=10)
    variation_type: Optional[str] = "tone"  # tone, length, angle

class ContentResponse(BaseModel):
    id: int
    campaign_id: int
    content_type: ContentType
    marketing_angle: MarketingAngle
    content_data: Dict[str, Any]
    compliance_status: ComplianceStatus
    compliance_notes: Optional[str] = None
    version: int
    parent_content_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# INTELLIGENCE SCHEMAS
# ============================================================================

class IntelligenceCompileRequest(BaseModel):
    campaign_id: int
    deep_research: bool = False
    include_competitors: bool = True

class IntelligenceResponse(BaseModel):
    campaign_id: int
    product_info: Dict[str, Any]
    competitor_analysis: Optional[List[Dict[str, Any]]] = None
    market_insights: Optional[Dict[str, Any]] = None
    recommended_angles: List[MarketingAngle]
    compiled_at: datetime

class KnowledgeBaseEntry(BaseModel):
    campaign_id: int
    content: str
    meta_data: Optional[Dict[str, Any]] = None
    source_url: Optional[HttpUrl] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    campaign_id: int
    content_preview: str
    meta_data: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    campaign_id: int
    query: str
    top_k: int = Field(default=5, ge=1, le=20)

class RAGQueryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    context_used: str

# ============================================================================
# COMPLIANCE SCHEMAS
# ============================================================================

class ComplianceCheckRequest(BaseModel):
    content: str
    content_type: ContentType
    affiliate_network: Optional[str] = None

class ComplianceCheckResponse(BaseModel):
    status: ComplianceStatus
    score: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    ftc_compliance: bool
    network_compliance: bool

class FTCGuidelinesResponse(BaseModel):
    guidelines: List[Dict[str, str]]
    last_updated: str
    source: str

# ============================================================================
# MEDIA SCHEMAS
# ============================================================================

class MediaUploadResponse(BaseModel):
    file_id: str
    file_url: str
    file_type: str
    file_size: int
    uploaded_at: datetime

# ============================================================================
# GENERIC RESPONSES
# ============================================================================

class MessageResponse(BaseModel):
    message: str
    detail: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)