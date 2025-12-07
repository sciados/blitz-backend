# /app/schemas.py

from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any, Union, Literal
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

# ============================================================================
# VIDEO SCRIPT ENUMS
# ============================================================================

class VideoType(str, Enum):
    """Types of videos for script generation"""

    # LOCAL BUSINESS VIDEO TYPES
    TESTIMONIAL = "testimonial"
    PROBLEM_SOLUTION = "problem_solution"
    TUTORIAL = "tutorial"
    BEFORE_AFTER = "before_after"
    BEHIND_SCENES = "behind_scenes"
    OWNER_INTRO = "owner_intro"
    EXPLAINER = "explainer"
    FAQ = "faq"

    # AFFILIATE MARKETING VIDEO TYPES
    PRODUCT_DEMO = "product_demo"
    COMPARISON = "comparison"
    UNBOXING = "unboxing"
    TRANSFORMATION = "transformation"
    PROBLEM_AGITATION = "problem_agitation"
    SOLUTION_PITCH = "solution_pitch"
    URGENCY = "urgency"
    STORYTELLING = "storytelling"

    # LEGACY/UNIVERSAL TYPES
    REVIEW = "review"
    COMMERCIAL = "commercial"
    INTERVIEW = "interview"

class VideoAtmosphere(str, Enum):
    """Atmosphere and mood for the video"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENERGETIC = "energetic"
    CALM = "calm"
    DRAMATIC = "dramatic"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    UPLIFTING = "uplifting"
    INTIMATE = "intimate"
    MYSTERIOUS = "mysterious"

class VideoLighting(str, Enum):
    """Lighting style for the video"""
    BRIGHT = "bright"
    SOFT = "soft"
    WARM = "warm"
    COOL = "cool"
    DRAMATIC = "dramatic"
    NATURAL = "natural"
    CINEMATIC = "cinematic"
    HIGH_CONTRAST = "high_contrast"
    MOOD = "mood"

class VideoStyle(str, Enum):
    """Overall visual style"""
    CORPORATE = "corporate"
    LIFESTYLE = "lifestyle"
    MINIMALIST = "minimalist"
    BOLD = "bold"
    RUSTIC = "rustic"
    MODERN = "modern"
    VINTAGE = "vintage"
    GRITTY = "gritty"
    CLEAN = "clean"

class VideoPace(str, Enum):
    """Pacing and rhythm of the video"""
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    DYNAMIC = "dynamic"

class VideoFormat(str, Enum):
    """Video format and duration"""
    SHORT_FORM = "short_form"  # 15-20 seconds (TikTok, Instagram Reels, YouTube Shorts)
    LONG_FORM = "long_form"    # 1+ minutes (YouTube, Facebook)
    STORY = "story"           # 15 seconds (Instagram Stories, Snapchat)

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
    # Video script specific parameters
    video_type: Optional[VideoType] = None
    video_format: Optional[VideoFormat] = Field(default=VideoFormat.LONG_FORM, description="short_form: 15-20s, long_form: 1+ min, story: 15s")
    video_atmosphere: Optional[VideoAtmosphere] = None
    video_lighting: Optional[VideoLighting] = None
    video_style: Optional[VideoStyle] = None
    video_pace: Optional[VideoPace] = None
    include_camera_angles: Optional[bool] = Field(default=True)
    include_visual_cues: Optional[bool] = Field(default=True)
    include_transitions: Optional[bool] = Field(default=True)
    target_platform: Optional[str] = Field(default="youtube", description="youtube, tiktok, instagram, facebook, linkedin")

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
    image_type: str  # Type of image (hero, product, social, ad, etc.)
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
    x: float = 0.0  # X position in pixels (supports sub-pixel precision)
    y: float = 0.0  # Y position in pixels (supports sub-pixel precision)
    font_size: int = 48
    font_family: str = "Arial"
    color: str = "#FFFFFF"
    stroke_color: Optional[str] = None
    stroke_width: int = 0
    opacity: float = 1.0  # 0.0 to 1.0
    z_index: int = 1  # Layer order (higher = on top)
    bold: bool = False  # Bold text style
    italic: bool = False  # Italic text style
    strikethrough: bool = False  # Strikethrough text style
    # Percentage-based positioning for consistent placement across image sizes
    x_percent: Optional[float] = None
    y_percent: Optional[float] = None
    font_size_percent: Optional[float] = None


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
    display_width: Optional[int] = None  # Optional: resize final image to this width
    display_height: Optional[int] = None  # Optional: resize final image to this height


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


class ImageOverlayLayer(BaseModel):
    """A single image layer to overlay on a base image."""
    image_url: str
    x: float = 0.0  # X position in pixels
    y: float = 0.0  # Y position in pixels
    scale: float = 1.0  # Scale factor (1.0 = original size)
    rotation: float = 0.0  # Rotation in degrees
    opacity: float = 1.0  # 0.0 to 1.0
    z_index: int = 1  # Layer order (higher = on top)


class ImageImageOverlayRequest(BaseModel):
    """Request to add image overlay to a base image."""
    image_url: str  # Base image URL
    image_overlays: List[ImageOverlayLayer]
    campaign_id: Optional[int] = None
    image_type: str = "social"
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"
    provider: str = "manual"
    model: str = "image_overlay"
    prompt: str = "Image with image overlay"
    display_width: Optional[int] = None  # Optional: resize final image to this width
    display_height: Optional[int] = None  # Optional: resize final image to this height


class ImageImageOverlayResponse(BaseModel):
    """Response from image overlay operation."""
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
    ai_generation_cost: Optional[float] = 0.0  # Image overlay is free
    created_at: Optional[datetime] = None


class ImageTrimRequest(BaseModel):
    """Request to trim transparent pixels from an image."""
    image_url: str
    padding: int = 5  # Transparent border to keep around content
    campaign_id: Optional[int] = None  # For R2 storage path


class ImageTrimResponse(BaseModel):
    """Response from trim operation."""
    image_url: str
    original_width: int
    original_height: int
    trimmed_width: int
    trimmed_height: int


class ImageCompositeRequest(BaseModel):
    """Request to composite multiple text and image layers onto a base image."""
    image_url: str  # Base image URL
    text_layers: List[TextLayer] = []  # Text layers to overlay
    image_layers: List[ImageOverlayLayer] = []  # Image layers to overlay
    campaign_id: Optional[int] = None
    image_type: str = "social"
    style: str = "photorealistic"
    aspect_ratio: str = "1:1"
    provider: str = "manual"
    model: str = "composite"
    prompt: str = "Composite image with text and image layers"


class ImageCompositeResponse(BaseModel):
    """Response from composite operation."""
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
    ai_generation_cost: Optional[float] = 0.0
    created_at: Optional[datetime] = None


# ============================================================================
# ADMIN SCHEMAS
# ============================================================================

class ImageTypeUpdateRequest(BaseModel):
    """Request to update an image's type."""
    image_type: str  # The new image_type (hero, product, social, ad, etc.)

# ============================================================================
# EMAIL SIGNUP SCHEMAS (Pre-launch Signups)
# ============================================================================

class AudienceType(str, Enum):
    PRODUCT_DEV = "product-dev"
    AFFILIATE = "affiliate"
    BUSINESS = "business"

class EmailSignupBase(BaseModel):
    email: EmailStr
    audience_type: AudienceType
    source: Optional[str] = "coming-soon"

class EmailSignupCreate(EmailSignupBase):
    """Schema for creating a new email signup."""
    pass

class EmailSignupResponse(EmailSignupBase):
    """Schema for email signup response."""
    id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    notified: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# EMAIL TEMPLATE SCHEMAS
# ============================================================================

class EmailTemplateBase(BaseModel):
    """Base schema for email templates."""
    name: str
    description: Optional[str] = None
    audience_type: Optional[Literal["product-dev", "affiliate", "business"]] = None
    subject: str
    html_content: str
    text_content: Optional[str] = None
    is_active: bool = True

class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating a new email template."""
    is_default: bool = False

class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template."""
    name: Optional[str] = None
    description: Optional[str] = None
    audience_type: Optional[Literal["product-dev", "affiliate", "business"]] = None
    subject: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class EmailTemplateResponse(EmailTemplateBase):
    """Schema for email template response."""
    id: int
    is_default: bool
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    """Schema for signup statistics."""
    total_signups: int
    product_dev: int
    affiliate: int
    business: int
    last_24h: int


# ============================================================================
# INTERNAL MESSAGING SYSTEM SCHEMAS
# ============================================================================

class MessageType(str, Enum):
    """Message types for internal messaging."""
    ADMIN_BROADCAST = "ADMIN_BROADCAST"
    ADMIN_GROUP = "ADMIN_GROUP"
    DEV_TO_AFFILIATES = "DEV_TO_AFFILIATES"
    AFFILIATE_REQUEST_DEV = "AFFILIATE_REQUEST_DEV"
    AFFILIATE_RESPONSE = "AFFILIATE_RESPONSE"
    AFFILIATE_REQUEST_AFFILIATE = "AFFILIATE_REQUEST_AFFILIATE"
    AFFILIATE_AFFILIATE_RESPONSE = "AFFILIATE_AFFILIATE_RESPONSE"
    USER_TO_USER = "USER_TO_USER"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"


class MessageBase(BaseModel):
    """Base message schema."""
    subject: str
    content: str
    message_type: MessageType
    parent_message_id: Optional[int] = None


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    recipient_ids: List[int]  # List of recipient user IDs
    is_broadcast: bool = False
    broadcast_group: Optional[str] = None  # For group broadcasts (all_connections, all_affiliates, all_creators)


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    sender_id: int
    is_broadcast: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageDetailResponse(MessageResponse):
    """Detailed message response with recipients."""
    recipients: List[Dict[str, Any]] = []
    read_receipts: List[Dict[str, Any]] = []
    parent_message: Optional[MessageResponse] = None


class MessageRecipientUpdate(BaseModel):
    """Schema for updating message recipient status."""
    status: Optional[str] = None  # read, archived


class MessageRequestType(str, Enum):
    """Message request types."""
    AFFILIATE_TO_DEV = "AFFILIATE_TO_DEV"
    AFFILIATE_TO_AFFILIATE = "AFFILIATE_TO_AFFILIATE"
    DEV_TO_AFFILIATE = "DEV_TO_AFFILIATE"
    CREATOR_TO_CREATOR = "CREATOR_TO_CREATOR"


class MessageRequestStatus(str, Enum):
    """Message request statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class MessageRequestBase(BaseModel):
    """Base message request schema."""
    recipient_id: int
    message_type: MessageRequestType
    subject: str
    content: str


class MessageRequestCreate(MessageRequestBase):
    """Schema for creating a new message request."""
    pass


class MessageRequestResponse(MessageRequestBase):
    """Schema for message request response."""
    id: int
    sender_id: int
    status: MessageRequestStatus
    created_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageRequestUpdate(BaseModel):
    """Schema for updating a message request."""
    status: MessageRequestStatus


class AffiliateProfileBase(BaseModel):
    """Base affiliate profile schema."""
    bio: Optional[str] = None
    specialty: Optional[str] = None
    years_experience: Optional[int] = None
    website_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    stats: Optional[Dict[str, Any]] = None


class AffiliateProfileCreate(AffiliateProfileBase):
    """Schema for creating an affiliate profile."""
    pass


class AffiliateProfileUpdate(BaseModel):
    """Schema for updating an affiliate profile."""
    bio: Optional[str] = None
    specialty: Optional[str] = None
    years_experience: Optional[int] = None
    website_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    stats: Optional[Dict[str, Any]] = None


class AffiliateProfileResponse(AffiliateProfileBase):
    """Schema for affiliate profile response."""
    id: int
    user_id: int
    reputation_score: int
    verified: bool
    created_at: datetime
    updated_at: datetime

    # User information
    email: str
    full_name: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class AffiliateSearchResponse(BaseModel):
    """Schema for affiliate search results."""
    id: int
    user_id: int
    email: str
    full_name: Optional[str] = None
    user_type: Optional[str] = None
    profile_image_url: Optional[str] = None
    specialty: Optional[str] = None
    years_experience: Optional[int] = None
    reputation_score: int
    verified: bool
    is_connected: bool = False
    mutual_products: List[str] = []


class ConnectionType(str, Enum):
    """Connection types."""
    MUTUAL_PRODUCT = "mutual_product"
    APPROVED_REQUEST = "approved_request"
    MUTUAL_CONNECTION = "mutual_connection"
    BLOCKED = "blocked"


class AffiliateConnectionBase(BaseModel):
    """Base affiliate connection schema."""
    user2_id: int  # The other user ID
    connection_type: ConnectionType


class AffiliateConnectionResponse(AffiliateConnectionBase):
    """Schema for affiliate connection response."""
    id: int
    user1_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InboxResponse(BaseModel):
    """Schema for inbox messages."""
    messages: List[MessageDetailResponse]
    total: int
    unread_count: int


class SentMessagesResponse(BaseModel):
    """Schema for sent messages."""
    messages: List[MessageResponse]
    total: int


class ComposeMessageRequest(BaseModel):
    """Schema for composing a message."""
    recipient_type: Literal["user", "affiliates", "all"]
    recipient_ids: Optional[List[int]] = None
    subject: str
    content: str
    message_type: MessageType = MessageType.USER_TO_USER


class MessageThreadResponse(BaseModel):
    """Schema for a message thread."""
    thread_id: int
    subject: str
    participants: List[Dict[str, Any]]
    messages: List[MessageDetailResponse]
    created_at: datetime
    updated_at: datetime


class MessageStatistics(BaseModel):
    """Schema for message statistics."""
    total_messages: int
    unread_messages: int
    sent_messages: int
    pending_requests: int
    approved_requests: int

