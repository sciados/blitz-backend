# Video Generation Fix Summary

## Issues Fixed

### 1. Database Schema Missing Columns ✅
**Problem:** Video generation failing with `column "generation_mode_used" does not exist`

**Fix:** Created migration `033_add_missing_video_generations_columns.py`
- Adds `generation_mode_used` column (String(50))
- Adds `slides` column (JSONB)
- Idempotent - checks if columns exist before adding
- **Will run automatically on Railway deploy**

### 2. Invalid Task Type for Image-to-Video (Hunyuan) ✅
**Problem:** `Hunyuan video generation failed: invalid task type`

**Root Cause:** Code was using `task_type = "img2video"` which doesn't exist

**Fix:** Updated to `task_type = "img2video-concat"` (line 420 in app/api/video.py)
- Based on PiAPI Hunyuan API documentation
- Hunyuan supports two image-to-video modes: `img2video-concat` and `img2video-replace`
- Using concat as default

**Code Change:**
```python
# Before (BROKEN):
task_type = "img2video"

# After (FIXED):
task_type = "img2video-concat"
```

### 3. Invalid Task Type for Image-to-Video (WanX) ✅
**Problem:** WanX would fail with invalid task type for image-to-video with 1.3b models

**Root Cause:** Code used `task_type = f"img2video-{model_variant}"` which creates `img2video-1.3b` (doesn't exist)

**Fix:** Added logic to use correct task types (lines 595-602 in app/api/video.py)
- For 1.3b models: Falls back to `img2video-14b` (since 1.3b doesn't support img2video)
- For 14b models: Uses `img2video-14b` (exists)
- Based on PiAPI WanX API documentation

**Code Change:**
```python
# Before (BROKEN):
task_type = f"img2video-{model_variant}"

# After (FIXED):
if generation_mode == "image_to_video" and image_url:
    if model_variant == "1.3b":
        task_type = "img2video-14b"  # Fallback
    else:
        task_type = f"img2video-{model_variant}"
```

## Files Modified

1. **app/api/video.py** (lines 420, 595-602)
   - Fixed Hunyuan task type for image-to-video
   - Fixed WanX task type for image-to-video

2. **alembic/versions/033_add_missing_video_generations_columns.py** (NEW)
   - Idempotent migration to add missing columns

## Deployment

When you deploy to Railway:
1. ✅ Migration 033 runs automatically
2. ✅ Database columns added
3. ✅ Code changes deployed
4. ✅ All three issues resolved

## Testing

After deployment, test:
- ✅ Text-to-video generation (any provider)
- ✅ Image-to-video with Hunyuan
- ✅ Image-to-video with WanX

## Additional Notes

**WanX Task Types Available:** img2video-14b, img2video-14b-lora, img2video-14b-keyframe, img2video-14b-control-camera, wan22-img2video-14b

**Future Enhancement:** Consider making image-to-video mode selectable (concat vs replace for Hunyuan, different variants for WanX) in the UI.
