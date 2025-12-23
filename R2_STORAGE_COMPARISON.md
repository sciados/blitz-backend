# R2 Storage: Old vs New Approach

## Summary

I've created a **centralized R2 storage utility** that provides a cleaner, more consistent interface for all R2 operations. This eliminates hardcoded paths and provides a single source of truth for file organization.

## Files Created

1. **`app/services/r2_storage.py`** - New centralized utility
2. **`R2_STORAGE_USAGE.md`** - Usage documentation
3. **`R2_STORAGE_COMPARISON.md`** - This comparison document

## Comparison: Old vs New

### OLD Approach (Hardcoded Paths)

```python
# ImageGenerator - save_draft_image()
filename = f"draft_{int(time.time())}_{hashlib.md5(image_url.encode()).hexdigest()[:8}.png"
r2_key, saved_image_url = await self.r2_storage.upload_file(
    file_bytes=image_data,
    key=f"campaignforge-storage/campaigns/{campaign_id}/edited/{filename}",
    content_type="image/png"
)

# Image Editor Plugin
r2_path = f"campaigns/{campaign_id}/edited/{timestamp}_{operation}_{base_name}.{extension}"
await r2_service.upload_edited_image(...)

# API Endpoints
key=f"campaignforge-storage/campaigns/{campaign_id}/generated_files/{filename}"
```

**Problems:**
- ❌ Hardcoded paths everywhere
- ❌ Inconsistent path structure
- ❌ No central place to change organization
- ❌ Repetitive code
- ❌ Easy to make mistakes

### NEW Approach (Centralized Utility)

```python
from app.services.r2_storage import r2_storage

# Simple upload with automatic path construction
filename = R2Storage.generate_image_filename(
    operation="overlay",
    original_filename="base.png",
    campaign_id=campaign_id
)

r2_path, public_url = await r2_storage.upload_image(
    campaign_id=campaign_id,
    folder="edited",
    filename=filename,
    image_bytes=image_data
)

# That's it! Path is: "campaignforge-storage/campaigns/{id}/edited/{filename}"
```

**Benefits:**
- ✅ No hardcoded paths
- ✅ Consistent organization
- ✅ Single place to change structure
- ✅ Reusable methods
- ✅ Type-safe folder names
- ✅ Automatic filename generation
- ✅ Clean, readable code

## Migration Path

### Step 1: Use the New Utility

Instead of:
```python
key=f"campaignforge-storage/campaigns/{campaign_id}/edited/{filename}"
```

Use:
```python
from app.services.r2_storage import r2_storage

r2_path = r2_storage.construct_path(campaign_id, "edited", filename)
```

### Step 2: Use Convenience Methods

Instead of:
```python
await r2_storage.upload_file(
    campaign_id=campaign_id,
    folder="edited",
    filename=filename,
    file_bytes=image_data,
    content_type="image/png"
)
```

Use:
```python
await r2_storage.upload_image(
    campaign_id=campaign_id,
    folder="edited",
    filename=filename,
    image_bytes=image_data
)
```

### Step 3: Use Filename Generators

Instead of:
```python
filename = f"draft_{int(time.time())}_{hash}.png"
```

Use:
```python
filename = R2Storage.generate_filename("draft", "png", campaign_id)
```

## Centralized Features

### 1. Path Construction
```python
path = r2_storage.construct_path(
    campaign_id=28,
    folder="edited",
    filename="image.png"
)
# Returns: "campaignforge-storage/campaigns/28/edited/image.png"
```

### 2. Upload Methods
```python
# Generic upload
r2_path, url = await r2_storage.upload_file(...)

# Image upload
r2_path, url = await r2_storage.upload_image(...)

# Video upload
r2_path, url = await r2_storage.upload_video(...)

# Document upload
r2_path, url = await r2_storage.upload_document(...)
```

### 3. Filename Generation
```python
# Standard filename
filename = R2Storage.generate_filename("draft", "png", 28)
# Returns: "draft_20241223_143055_a1b2c3d4.png"

# Image operation filename
filename = R2Storage.generate_image_filename("inpaint", "base.png", 28)
# Returns: "inpaint_20241223_143055_a1b2c3d4_base.png"
```

### 4. Download
```python
file_bytes = await r2_storage.download_file(r2_path)
```

## Organization Structure

All files follow this structure:
```
campaignforge-storage/
  campaigns/
    {campaign_id}/
      generated_files/          # AI-generated images
        {filename}
        thumbnails/
          {filename}
        temp/
          {filename}
      edited/                   # Manually edited images
        {filename}
      videos/                   # Video files
        {filename}
      documents/                # PDFs, docs
        {filename}
```

## When to Use Each Approach

### Use New Utility For:
- ✅ New features
- ✅ Refactoring existing code
- ✅ Any upload/download operation
- ✅ Path construction

### Keep Old Approach For:
- ⚠️ Code that already works and won't be changed soon
- ⚠️ Third-party integrations
- ⚠️ Legacy endpoints

## Next Steps

1. **Review the utility** (`app/services/r2_storage.py`)
2. **Read the usage guide** (`R2_STORAGE_USAGE.md`)
3. **Start using it** for new code
4. **Refactor existing code** when convenient

## Example: Refactoring save_draft_image

**Before:**
```python
async def save_draft_image(...):
    filename = f"draft_{int(time.time())}_{hash}.png"
    r2_key, saved_image_url = await self.r2_storage.upload_file(
        file_bytes=image_data,
        key=f"campaignforge-storage/campaigns/{campaign_id}/edited/{filename}",
        content_type="image/png"
    )
```

**After:**
```python
async def save_draft_image(...):
    from app.services.r2_storage import r2_storage

    filename = R2Storage.generate_filename("draft", "png", campaign_id)
    r2_key, saved_image_url = await r2_storage.upload_image(
        campaign_id=campaign_id,
        folder="edited",
        filename=filename,
        image_bytes=image_data
    )
```

Much cleaner! 🎉
