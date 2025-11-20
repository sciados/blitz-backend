# app/schemas.py
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class ContentType(str, Enum):
    ARTICLE = "article"
    EMAIL = "email"
    EMAIL_SEQUENCE = "email_sequence"
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
    role: str
    user_type: str  # product_creator | affiliate_marketer
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
    product_url: Optional[HttpUrl] = None  # Optional - can create campaign before choosing product
    affiliate_network: Optional[str] = None
    commission_rate: Optional[str] = None  # "50%", "$37/sale", etc.
    affiliate_link: Optional[str] = None  # Optional - user's affiliate URL (auto-shortened)
    keywords: Optional[List[str]] = []
    product_description: Optional[str] = None
    product_type: Optional[str] = None
    target_audience: Optional[str] = None
    marketing_angles: Optional[List[MarketingAngle]] = []

class CampaignCreate(CampaignBase):
    """Create campaign with optional product URL (can be added later)"""
    product_intelligence_id: Optional[int] = None  # Link to Product Library when creating from product

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    product_url: Optional[HttpUrl] = None
    affiliate_network: Optional[str] = None
    commission_rate: Optional[str] = None
    affiliate_link: Optional[str] = None  # Update affiliate link (will auto-shorten)
    status: Optional[CampaignStatus] = None
    keywords: Optional[List[str]] = None
    product_description: Optional[str] = None
    product_type: Optional[str] = None
    target_audience: Optional[str] = None
    marketing_angles: Optional[List[MarketingAngle]] = None

class CampaignResponse(CampaignBase):
    id: int
    user_id: int
    status: CampaignStatus
    product_intelligence_id: Optional[int] = None  # Link to product library
    affiliate_link_short_code: Optional[str] = None  # Shortened link code
    intelligence_data: Optional[Dict[str, Any]] = None
    thumbnail_image_url: Optional[str] = None  # Product thumbnail from ProductIntelligence
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
    length: Optional[Union[str, int]] = "medium"  # short/medium/long or custom word count (int)
    # Email sequence configuration
    num_emails: Optional[int] = Field(default=5, ge=3, le=10)
    sequence_type: Optional[str] = Field(default="cold_to_hot")  # cold_to_hot, warm_to_hot, hot_close

class ContentRefineRequest(BaseModel):
    refinement_instructions: str

class ContentVariationRequest(BaseModel):
    num_variations: int = Field(default=3, ge=1, le=10)
    variation_type: Optional[str] = "tone"  # tone, length, angle

class ContentResponse(BaseModel):
    id: int
    campaign_id: int
    content_type: ContentType
    marketing_angle: MarketingAngle
    content_data: Dict[str, Any]
    compliance_status: ComplianceStatus
    compliance_score: Optional[float] = None
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
    product_category: Optional[str] = None

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
# ============================================================================
# IMAGE GENERATION SCHEMAS
# ============================================================================

class ImageType(str, Enum):
    HERO = "hero"
    PRODUCT = "product"
    SOCIAL = "social"
    AD = "ad"
    EMAIL = "email"
    BLOG = "blog"
    INFOGRAPHIC = "infographic"
    COMPARISON = "comparison"
    VARIATION = "variation"

class ImageStyle(str, Enum):
    PHOTOREALISTIC = "photorealistic"
    ARTISTIC = "artistic"
    MINIMALIST = "minimalist"
    LIFESTYLE = "lifestyle"
    PRODUCT = "product"
    ILLUSTRATION = "illustration"
    RETRO = "retro"
    MODERN = "modern"

class AspectRatio(str, Enum):
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    WIDE = "21:9"
    CLASSIC = "4:3"

class ImageGenerateRequest(BaseModel):
    campaign_id: int
    image_type: ImageType
    style: Optional[ImageStyle] = ImageStyle.PHOTOREALISTIC
    aspect_ratio: Optional[AspectRatio] = AspectRatio.SQUARE
    custom_prompt: Optional[str] = None
    highlight_features: Optional[List[str]] = None
    use_testimonial: Optional[str] = None
    include_text_overlay: Optional[str] = None
    overlay_position: Optional[str] = "center"
    platform: Optional[str] = None
    quality_boost: Optional[bool] = False

class ImageBatchRequest(BaseModel):
    campaign_id: int
    images: List[Dict[str, Any]]
    batch_name: Optional[str] = None

class ImageVariationRequest(BaseModel):
    base_image_id: int
    num_variations: int = Field(default=3, ge=1, le=10)
    variation_type: Optional[str] = "style"
    variation_strength: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)

class ImageResponse(BaseModel):
    id: int
    campaign_id: int
    image_type: ImageType
    image_url: str
    thumbnail_url: Optional[str]
    provider: str
    model: str
    prompt: str
    style: ImageStyle
    aspect_ratio: AspectRatio
    metadata: Optional[Dict[str, Any]] = None
    ai_generation_cost: Optional[float] = None
    content_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ImageListResponse(BaseModel):
    images: List[ImageResponse]
    total: int
    page: int
    per_page: int

class ImageDeleteResponse(BaseModel):
    message: str
    deleted_id: int


class ImageUpgradeRequest(BaseModel):
    """Request to upgrade a draft image to premium quality."""
    campaign_id: int
    draft_image_url: str  # URL of the draft image to enhance
    custom_prompt: Optional[str] = None  # Optional enhancement prompt
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"
    quality_boost: Optional[bool] = True  # Default to quality boost for premium


class ImageSaveDraftRequest(BaseModel):
    """Request to save a draft image to the library."""
    campaign_id: int
    image_url: str  # URL of the draft image to save
    image_type: str
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"
    custom_prompt: Optional[str] = None
    provider: str
    model: str
    prompt: str


class TextLayer(BaseModel):
    """A single text layer to overlay on an image."""
    text: str
    x: int = 0  # X position in pixels
    y: int = 0  # Y position in pixels
    font_size: int = 48
    font_family: str = "Arial"
    color: str = "#FFFFFF"
    stroke_color: Optional[str] = None
    stroke_width: int = 0
    opacity: float = 1.0  # 0.0 to 1.0


class ImageTextOverlayRequest(BaseModel):
    """Request to add text overlay to an image."""
    image_url: str
    text_layers: List[TextLayer]
    campaign_id: Optional[int] = None
    image_type: str = "social"
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"
    provider: str = "manual"
    model: str = "text_overlay"
    prompt: str = "Image with text overlay"


class ImageTextOverlayResponse(BaseModel):
    """Response from text overlay operation."""
    id: int
    campaign_id: Optional[int]
    image_type: str
    image_url: str
    thumbnail_url: Optional[str]
    provider: str
    model: str
    prompt: str
    style: str
    aspect_ratio: str
    metadata: Optional[Dict[str, Any]] = None
    ai_generation_cost: Optional[float] = 0.0  # Text overlay is free
    created_at: Optional[datetime] = None
