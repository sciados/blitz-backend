# R2 Storage Utility - Usage Guide

## Overview

The centralized `R2Storage` utility provides a unified interface for all R2 operations across the application. No more hardcoded paths!

## Quick Start

```python
from app.services.r2_storage import r2_storage

# Upload an image to the "edited" folder
r2_path, public_url = await r2_storage.upload_image(
    campaign_id=28,
    folder="edited",
    filename="inpaint_result.png",
    image_bytes=image_data,
    content_type="image/png"
)

# Download a file
file_bytes = await r2_storage.download_file(r2_path)
```

## Path Construction

The utility automatically handles path construction using the base path `campaignforge-storage`:

```
campaignforge-storage/campaigns/{campaign_id}/{folder}/{filename}
```

### Supported Folders

| Folder | Path | Use Case |
|--------|------|----------|
| `generated_files` | `campaignforge-storage/campaigns/{id}/generated_files/` | AI-generated images |
| `edited` | `campaignforge-storage/campaigns/{id}/edited/` | Manually edited images |
| `thumbnails` | `campaignforge-storage/campaigns/{id}/generated_files/thumbnails/` | Image thumbnails |
| `temp` | `campaignforge-storage/campaigns/{id}/generated_files/temp/` | Temporary files |
| `videos` | `campaignforge-storage/campaigns/{id}/videos/` | Video files |
| `documents` | `campaignforge-storage/campaigns/{id}/documents/` | PDF, docs, etc. |

## Common Use Cases

### 1. Save Overlay Image (NEW - Clean Approach)

**Before (Hardcoded Path):**
```python
r2_key, image_url = await r2_storage.upload_file(
    file_bytes=image_data,
    key=f"campaignforge-storage/campaigns/{campaign_id}/edited/{filename}",
    content_type="image/png"
)
```

**After (Using Utility):**
```python
# Generate filename
filename = R2Storage.generate_image_filename(
    operation="overlay",
    original_filename="base.png",
    campaign_id=campaign_id,
    extension="png"
)

# Upload using the utility
r2_path, public_url = await r2_storage.upload_image(
    campaign_id=campaign_id,
    folder="edited",
    filename=filename,
    image_bytes=image_data
)
```

### 2. Save Generated Image

```python
filename = R2Storage.generate_filename(
    prefix="generated",
    extension="png",
    campaign_id=campaign_id
)

r2_path, public_url = await r2_storage.upload_image(
    campaign_id=campaign_id,
    folder="generated_files",
    filename=filename,
    image_bytes=image_data
)
```

### 3. Save Thumbnail

```python
filename = R2Storage.generate_filename(
    prefix="thumb",
    extension="jpg",
    campaign_id=campaign_id
)

r2_path, public_url = await r2_storage.upload_image(
    campaign_id=campaign_id,
    folder="thumbnails",
    filename=filename,
    image_bytes=thumb_data,
    content_type="image/jpeg"
)
```

### 4. Upload Video

```python
filename = R2Storage.generate_filename(
    prefix="video",
    extension="mp4",
    campaign_id=campaign_id
)

r2_path, public_url = await r2_storage.upload_file(
    campaign_id=campaign_id,
    folder="videos",
    filename=filename,
    file_bytes=video_data,
    content_type="video/mp4"
)
```

## Benefits

1. **No Hardcoded Paths**: All paths constructed automatically
2. **Consistent Organization**: All files follow the same structure
3. **Easy to Maintain**: Change base path or folder structure in one place
4. **Type Safety**: Folder names validated against FOLDERS dict
5. **Filename Generation**: Automatic timestamp and hash generation
6. **Reusable**: Single instance used across the application

## Migration Guide

To migrate existing code:

1. Import the utility: `from app.services.r2_storage import r2_storage`
2. Replace hardcoded paths with utility calls
3. Use `generate_filename()` or `generate_image_filename()` for consistent naming
4. Use convenience methods (`upload_image`, `upload_video`, etc.) when possible

## File Structure After Migration

```
campaignforge-storage/
  campaigns/
    {campaign_id}/
      generated_files/
        20241223_143055_generated_a1b2c3d4.png
        20241223_143055_thumb_a1b2c3d4.jpg
        thumbnails/
          20241223_143055_thumb_a1b2c3d4.jpg
        temp/
          20241223_143055_draft_a1b2c3d4.png
      edited/
        20241223_143055_inpaint_base_a1b2c3d4.png
        20241223_143055_overlay_base_a1b2c3d4.png
      videos/
        20241223_143055_video_a1b2c3d4.mp4
      documents/
        20241223_143055_brochure_a1b2c3d4.pdf
```

## Best Practices

1. **Always use folder constants**: `"edited"`, `"generated_files"`, etc.
2. **Generate filenames**: Don't manually create filenames with timestamps
3. **Use convenience methods**: `upload_image()` instead of `upload_file()` for images
4. **Include campaign_id**: Always pass campaign_id for proper organization
5. **Set correct content_type**: Important for proper file serving
