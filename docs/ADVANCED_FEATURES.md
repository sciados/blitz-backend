# Advanced Features - Hunyuan & WanX

## Overview
This document outlines the advanced features available in Hunyuan Video and WanX that are NOT yet implemented but could be added in future iterations.

## Hunyuan Video - Advanced Features

### Available Task Types

1. **txt2video** (✅ Implemented)
   - Basic text-to-video generation
   - Parameters: `prompt`, `aspect_ratio`

2. **txt2video-lora** (🔄 Future Enhancement)
   - Text-to-video with LoRA fine-tuning
   - Parameters: `prompt`, `lora_settings[]`
     - `lora_type`: Style type (e.g., "anime")
     - `lora_strength`: Intensity (default: 1.0)
   - **Use Case**: Custom styles, brand-specific looks

3. **fast-txt2video** (🔄 Future Enhancement)
   - Accelerated text-to-video generation
   - **Cost**: Lower than standard (~$0.03 vs $0.09)
   - **Use Case**: High-volume, quick generations

4. **img2video-concat** (🔄 Future Enhancement)
   - Concatenates input image with motion
   - Parameters: `image`, `prompt`, `aspect_ratio`
   - **Use Case**: Animated images from static photos

5. **img2video-replace** (🔄 Future Enhancement)
   - Replaces subject in input image
   - Parameters: `image`, `prompt`, `aspect_ratio`
   - **Use Case**: Subject replacement in scenes

### LoRA Support
Hunyuan supports LoRA (Low-Rank Adaptation) for fine-tuned video generation:
- Custom style training
- Brand-specific aesthetics
- Anime, realistic, and custom styles
- Configurable strength parameters

## WanX - Advanced Features

### Camera Control (img2video-14b-control-camera)

Available Camera Movements:

**Zoom:**
- `zoom_in` (dolly in)
- `zoom_out` (dolly out)

**Pan (Pedestal & Truck):**
- `pan_left`, `pan_right`
- `pan_up`, `pan_down`

**Tilt (Pan & Tilt):**
- `tilt_left`, `tilt_right`
- `tilt_up`, `tilt_down`

**Roll:**
- `roll_clockwise`
- `roll_anticlockwise`

### Motion Parameters
Each camera movement requires:
- `motion_type`: The movement type (e.g., "zoom_in")
- `motion_speed`: Speed control (0.0-10.0, default: 0.2)

### Example Camera Control Request
```json
{
  "model": "Qubico/wanx",
  "task_type": "img2video-14b-control-camera",
  "input": {
    "image": "https://example.com/image.jpg",
    "prompt": "A cinematic shot of a product",
    "negative_prompt": "blurry, low quality",
    "control_camera_settings": [
      {
        "motion_type": "zoom_in",
        "motion_speed": 0.2
      }
    ]
  }
}
```

### WanX Task Types Summary
- `txt2video-1.3b` ✅ (Implemented)
- `txt2video-14b` ✅ (Implemented)
- `txt2video-14b-lora` 🔄 (Future)
- `img2video-14b` 🔄 (Future)
- `img2video-14b-lora` 🔄 (Future)
- `img2video-14b-keyframe` 🔄 (Future)
- `img2video-14b-control-camera` 🔄 (Advanced - Camera Control)
- `wan22-txt2video-14b` 🔄 (Future - Wan2.2 Model)
- `wan22-img2video-14b` 🔄 (Future - Wan2.2 Model)

### Wan2.2 Models (Future)
- Generate 720p resolution (vs 480p standard)
- Improved quality and motion handling
- Same pricing structure

## Implementation Status

### ✅ Currently Implemented
- **Hunyuan**: Basic txt2video and img2video
- **WanX**: Basic txt2video with 1.3b and 14b models
- Both use standard PiAPI endpoint `/api/v1/task`
- Full database tracking and status polling
- Background task monitoring

### 🔄 Future Enhancements (Priority Order)

1. **High Priority**
   - Hunyuan fast-txt2video (cost savings)
   - WanX img2video support (image-to-video)

2. **Medium Priority**
   - Hunyuan LoRA support (custom styles)
   - WanX 14b LoRA support
   - WanX keyframe control

3. **Low Priority (Advanced)**
   - WanX camera control (cinematic shots)
   - Wan2.2 models (720p)
   - Hunyuan img2video-concat/replace

## When to Use Advanced Features

### LoRA (Hunyuan/WanX)
- **Use Case**: Brand consistency, custom aesthetics
- **Requirements**: Pre-trained LoRA models
- **Cost**: Same base price + LoRA processing

### Camera Control (WanX)
- **Use Case**: Professional cinematography, product demos
- **Requirements**: Image input, specific camera movements
- **Cost**: Standard WanX pricing

### Fast Mode (Hunyuan)
- **Use Case**: High-volume, quick iterations
- **Requirements**: None
- **Cost**: ~67% cheaper than standard

### Image-to-Video (Both)
- **Use Case**: Animating existing images
- **Requirements**: High-quality input image
- **Cost**: Same as text-to-video

## API Extensions Needed

To support these features, the following could be added to `VideoGenerateRequest`:

```python
class VideoGenerateRequest(BaseModel):
    # ... existing fields ...

    # Advanced features (optional)
    lora_settings: Optional[List[Dict[str, Any]]] = None
    camera_movements: Optional[List[Dict[str, Any]]] = None
    negative_prompt: Optional[str] = None
    image_to_video_mode: Optional[str] = Field(None, description="concat or replace")
```

## Testing Advanced Features

Once implemented, test with:

```bash
# Test Hunyuan Fast
curl -X POST http://localhost:8000/api/video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "123",
    "generation_mode": "text_to_video",
    "script": "Quick product demo",
    "style": "marketing",
    "duration": 5,
    "aspect_ratio": "16:9",
    "provider": "piapi_hunyuan_fast"
  }'

# Test WanX with Image
curl -X POST http://localhost:8000/api/video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "123",
    "generation_mode": "image_to_video",
    "image_url": "https://example.com/product.jpg",
    "script": "Product showcase with zoom",
    "style": "marketing",
    "duration": 5,
    "aspect_ratio": "16:9",
    "provider": "piapi_wanx_14b"
  }'
```

## Conclusion

The current implementation provides a solid foundation with cost-effective video generation. Advanced features can be added incrementally based on user needs and use cases.

**Priority for Implementation:**
1. Hunyuan fast-txt2video (immediate cost savings)
2. Image-to-video support for both providers
3. LoRA support for custom styles
4. Camera control for professional cinematography
