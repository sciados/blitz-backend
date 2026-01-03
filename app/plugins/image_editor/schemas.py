"""
Pydantic schemas for Image Editor Plugin
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


class ImageSource(str, Enum):
    """Image source types for unified image responses"""
    GENERATED = "generated"  # AI-generated from prompt
    EDITED = "edited"        # Edited from another image
    UPLOADED = "uploaded"    # User-uploaded (future)
    STOCK = "stock"          # Stock library (future)


class OperationType(str, Enum):
    """Supported image editing operations"""
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"
    BACKGROUND_REMOVAL = "background_removal"
    BACKGROUND_ADD = "background_add"
    BACKGROUND = "background"  # Legacy support for old images
    UPSCALING = "upscaling"
    SEARCH_REPLACE = "search_replace"
    RELIGHT = "relight"
    ERASE = "erase"
    SKETCH_TO_IMAGE = "sketch_to_image"
    COLLAGE = "collage"
    TEMPLATE = "template"
    FRAME = "frame"
    LANDING_PAGE = "landing_page"


class InpaintingRequest(BaseModel):
    """Request schema for inpainting operation"""
    image_url: str = Field(..., description="URL/path of the image to edit")
    campaign_id: int = Field(..., description="Campaign ID for organizing edited images")
    prompt: str = Field(..., description="What to paint/add in the masked area")
    mask_image_data: str = Field(..., description="Base64 encoded mask image (white = edit area)")
    negative_prompt: Optional[str] = Field(None, description="What to avoid in the generation")
    seed: Optional[int] = Field(0, description="Seed for reproducibility")
    output_format: str = Field("png", description="Output format: png, jpeg, webp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://r2.example.com/campaigns/123/image.png",
                "campaign_id": 123,
                "prompt": "a red sports car",
                "mask_image_data": "base64_encoded_mask_data_here",
                "negative_prompt": "blurry, low quality",
                "seed": 12345,
                "output_format": "png"
            }
        }


class InpaintingResponse(BaseModel):
    """Response schema for inpainting operation"""
    success: bool
    edited_image_url: Optional[str] = None
    edited_image_path: Optional[str] = None
    original_image_path: str
    edit_id: int
    processing_time_ms: int
    error_message: Optional[str] = None


class ImageEditRecord(BaseModel):
    """Database record for an image edit"""
    id: int
    source: str = "edited"  # Image source type (for unified responses)
    user_id: int
    campaign_id: int
    original_image_path: str
    edited_image_path: str
    operation_type: OperationType
    operation_params: Optional[Dict[str, Any]] = None
    stability_model: Optional[str] = None
    api_cost_credits: Optional[float] = None
    processing_time_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    # Parent-child relationship for tracking image lineage
    parent_image_id: Optional[int] = None
    # Transparency detection
    has_transparency: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EditStatistics(BaseModel):
    """Statistics for user's editing activity"""
    total_edits: int
    successful_edits: int
    failed_edits: int
    total_api_cost_credits: float  # Changed from total_credits_used
    average_processing_time_ms: int  # Changed from avg_processing_time_ms (float → int)


class EditHistoryResponse(BaseModel):
    """Response for fetching edit history"""
    edits: list[ImageEditRecord]
    statistics: EditStatistics


class UnifiedImageResponse(BaseModel):
    """
    Unified response for all image types (generated + edited)
    Provides consistent interface with source type identification
    """
    # Core fields (all images)
    id: int
    source: ImageSource              # Type identifier (generated/edited)
    image_url: str
    thumbnail_url: Optional[str] = None
    campaign_id: int
    created_at: datetime
    has_transparency: bool = False
    
    # Generated-specific fields (optional)
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    style: Optional[str] = None
    aspect_ratio: Optional[str] = None
    
    # Edited-specific fields (optional)
    operation_type: Optional[str] = None
    parent_image_id: Optional[int] = None
    processing_time_ms: Optional[int] = None
    original_image_path: Optional[str] = None
    
    # Common metadata
    cost_credits: Optional[float] = None
    
    class Config:
        use_enum_values = True
        from_attributes = True