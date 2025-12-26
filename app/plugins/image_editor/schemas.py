"""
Pydantic schemas for Image Editor Plugin
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class OperationType(str, Enum):
    """Supported image editing operations"""
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"
    BACKGROUND_REMOVAL = "background_removal"
    UPSCALING = "upscaling"
    SEARCH_REPLACE = "search_replace"
    RELIGHT = "relight"
    ERASE = "erase"
    SKETCH_TO_IMAGE = "sketch_to_image"
    COLLAGE = "collage"


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


class EditHistoryResponse(BaseModel):
    """Response for fetching edit history"""
    edits: list[ImageEditRecord]
    total: int
    page: int
    page_size: int


class EditStatistics(BaseModel):
    """Statistics for user's editing activity"""
    total_edits: int
    successful_edits: int
    failed_edits: int
    total_credits_used: float
    avg_processing_time_ms: float
    edits_by_type: Dict[str, int]
