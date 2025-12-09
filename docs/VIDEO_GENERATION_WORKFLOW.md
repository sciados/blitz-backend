# Video Generation Workflow Walkthrough

## Overview
This document provides a step-by-step walkthrough of how text-to-video and image-to-video generation works in Blitz.

## Architecture Overview

```
Frontend Request
    ↓
API Endpoint (/api/video/generate)
    ↓
Provider Selection (auto or forced)
    ↓
Service Class (LumaVideoService / HunyuanVideoService / WanxVideoService)
    ↓
PiAPI Request
    ↓
Database Record Creation
    ↓
Background Task (Status Polling)
    ↓
Status Updates
    ↓
Video Library Display
```

---

# 1. Text-to-Video Process

## Step 1: Frontend Request

**Endpoint:** `POST /api/video/generate`

**Request Body:**
```json
{
  "campaign_id": "123",
  "generation_mode": "text_to_video",
  "script": "Create an engaging marketing video about our new product launch with smooth transitions and professional visuals",
  "style": "marketing",
  "duration": 10,
  "aspect_ratio": "16:9",
  "provider": "piapi_hunyuan_fast"  // Optional: force specific provider
}
```

## Step 2: Backend Receives Request

**File:** `app/api/video.py` - `generate_video()` function

**What happens:**
1. ✅ Extract user_id and user_tier (currently mocked)
2. ✅ Validate PiAPI API key
3. ✅ Select provider based on duration and tier
4. ✅ Route to appropriate service class

## Step 3: Provider Selection

**File:** `app/api/video.py` - `select_video_provider()`

**Auto-Selection Logic:**
```python
if duration <= 10:
    return "piapi_hunyuan_fast"  # $0.03 - Most cost-effective
elif duration <= 60:
    return "piapi_wanx_1.3b"     # $0.12 - Best value
else:
    return "piapi_wanx_14b"      # $0.28 - Premium quality
```

**Forced Provider (if specified in request):**
```python
if forced_provider in ['piapi_hunyuan_fast', 'piapi_wanx_1.3b', ...]:
    return forced_provider
```

## Step 4: Service Execution

**Example: Hunyuan Video Service**

**File:** `app/api/video.py` - `HunyuanVideoService.generate_video()`

**Process:**
1. ✅ Prepare prompt:
   ```python
   def _prepare_prompt(self, script, style, duration):
       style_prompts = {
           "marketing": "Professional, engaging marketing video with smooth transitions",
           "educational": "Clear, informative educational video with clean visuals",
           "social": "Dynamic, eye-catching social media video optimized for mobile"
       }
       base_prompt = style_prompts.get(style, style_prompts["marketing"])
       return f"{base_prompt}. Duration: {duration}s. Script: {script}"
   ```

2. ✅ Build request to PiAPI:
   ```python
   request_data = {
       "model": "Qubico/hunyuan",
       "task_type": "txt2video",
       "input": {
           "prompt": "Professional, engaging marketing video with smooth transitions. Duration: 10s. Script: Create an engaging marketing video...",
           "aspect_ratio": "16:9"
       }
   }
   ```

3. ✅ Send to PiAPI:
   ```python
   response = await client.post(
       f"{self.base_url}/api/v1/task",
       headers={"x-api-key": self.api_key},
       json=request_data
   )
   ```

4. ✅ Receive task_id:
   ```python
   result = response.json()
   task_id = result.get("data", {}).get("task_id")
   # Example: "task_abc123def456"
   ```

## Step 5: Database Record Creation

**File:** `app/api/video.py` - `save_video_generation_to_db()`

**Database Entry:**
```python
video_gen = VideoGeneration(
    user_id=1,
    campaign_id=123,
    task_id="task_abc123def456",
    provider="piapi_hunyuan_fast",
    model_name="hunyuan-fast",
    generation_mode="text_to_video",
    script="Create an engaging marketing video...",
    style="marketing",
    aspect_ratio="16:9",
    requested_duration=10,
    actual_duration=5,  # Hunyuan always generates 5s
    status="processing",
    progress=0,
    cost=0.03,  # Based on model pricing
    created_at=datetime.utcnow()
)
```

## Step 6: Background Task Started

**Initiates Status Polling:**
```python
background_tasks.add_task(
    update_video_status_hunyuan,
    video_id=video_gen.id,
    db=db,
    video_service=hunyuan_service
)
```

## Step 7: Response to Frontend

**Immediate Response:**
```json
{
  "video_id": "1",
  "status": "processing",
  "duration": 5,
  "cost": 0.03,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Step 8: Background Status Polling

**File:** `app/api/video.py` - `update_video_status_hunyuan()`

**Polling Process:**
1. ✅ Get task_id from database
2. ✅ Poll PiAPI every 30 seconds:
   ```python
   response = await client.get(
       f"{self.base_url}/api/v1/task/{task_id}",
       headers={"x-api-key": self.api_key}
   )
   ```
3. ✅ Check status:
   - `pending` → `processing`
   - `processing` → `processing`
   - `completed` → `completed` ✅
   - `failed` → `failed` ❌

4. ✅ Update database when completed:
   ```sql
   UPDATE video_generations SET
     status = 'completed',
     progress = 100,
     video_url = 'https://...',
     thumbnail_url = 'https://...',
     completed_at = NOW()
   WHERE id = 1
   ```

## Step 9: Frontend Displays in Library

**File:** `src/app/(dashboard)/content/video/library/page.tsx`

**Video Library Display:**
```typescript
const videos = data?.videos || [];

return (
  <div>
    {videos.map(video => (
      <div key={video.id}>
        <img src={video.thumbnail_url} alt="Video thumbnail" />
        <h3>{video.generation_mode?.replace("_", " ").toUpperCase()}</h3>
        <p>Status: {video.status}</p>
        <p>Provider: {video.provider}</p>
        <p>Cost: ${video.cost}</p>
        {video.status === "completed" && video.video_url && (
          <a href={video.video_url} target="_blank">View Video</a>
        )}
      </div>
    ))}
  </div>
);
```

---

# 2. Image-to-Video Process

## Step 1: Frontend Request

**Endpoint:** `POST /api/video/generate`

**Request Body:**
```json
{
  "campaign_id": "123",
  "generation_mode": "image_to_video",
  "image_url": "https://example.com/product.jpg",
  "script": "Animate this product with subtle movement and professional lighting",
  "style": "marketing",
  "duration": 5,
  "aspect_ratio": "16:9",
  "provider": "piapi_wanx_1.3b"
}
```

## Step 2: Backend Receives Request

**Same as text-to-video, but `generation_mode = "image_to_video"`**

## Step 3: Provider Selection

**Same logic as text-to-video**

## Step 4: Service Execution

**Example: WanX Video Service**

**File:** `app/api/video.py` - `WanxVideoService.generate_video()`

**Process:**
1. ✅ Validate aspect ratio (WanX only supports 16:9 and 9:16):
   ```python
   if aspect_ratio not in ["16:9", "9:16"]:
       aspect_ratio = "16:9"  # Default fallback
   ```

2. ✅ Prepare prompt:
   ```python
   def _prepare_prompt(self, script, style, duration):
       style_prompts = {
           "marketing": "Professional, engaging marketing video with smooth transitions and high production value"
       }
       base_prompt = style_prompts.get(style, style_prompts["marketing"])
       return f"{base_prompt}. 5-second clip. Script: {script}"
   ```

3. ✅ Build request to PiAPI:
   ```python
   request_data = {
       "model": "Qubico/wanx",
       "task_type": "img2video-1.3b",  # Note: img2video, not txt2video
       "input": {
           "prompt": "Professional, engaging marketing video with smooth transitions and high production value. 5-second clip. Script: Animate this product...",
           "aspect_ratio": "16:9",
           "image": "https://example.com/product.jpg"  // Key difference!
       }
   }
   ```

4. ✅ Send to PiAPI and receive task_id (same as text-to-video)

## Step 5: Database Record Creation

**Similar to text-to-video, but:**
```python
video_gen = VideoGeneration(
    user_id=1,
    campaign_id=123,
    task_id="task_xyz789",
    provider="piapi_wanx_1.3b",
    model_name="wanx-1.3b",
    generation_mode="image_to_video",  // Different mode
    script="Animate this product with subtle movement...",
    style="marketing",
    aspect_ratio="16:9",
    requested_duration=5,
    actual_duration=5,
    status="processing",
    progress=0,
    cost=0.12,  # WanX pricing
    created_at=datetime.utcnow()
)
```

## Step 6: Background Task Started

**Initiates status polling for WanX:**
```python
background_tasks.add_task(
    update_video_status_wanx,
    video_id=video_gen.id,
    db=db,
    video_service=wanx_service
)
```

## Step 7-9: Same as Text-to-Video

- Background polling
- Status updates
- Video library display

---

# Key Differences: Text-to-Video vs Image-to-Video

| Aspect | Text-to-Video | Image-to-Video |
|--------|---------------|----------------|
| **Input** | Script/prompt only | Image URL + script/prompt |
| **Task Type** | `txt2video` | `img2video` |
| **API Param** | `input.prompt` | `input.prompt` + `input.image` |
| **Use Case** | Generate from scratch | Animate existing image |
| **Requirements** | Just text description | Valid image URL |
| **Examples** | "Create a product demo" | "Animate this photo of a product" |

---

# Database Schema

**Table: `video_generations`**

```sql
CREATE TABLE video_generations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    campaign_id INTEGER,
    task_id VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    generation_mode VARCHAR(50) NOT NULL,  -- text_to_video or image_to_video
    prompt TEXT,
    script TEXT,
    style VARCHAR(50),
    aspect_ratio VARCHAR(10),
    requested_duration INTEGER,
    actual_duration INTEGER,
    video_url TEXT,
    video_raw_url TEXT,
    thumbnail_url TEXT,
    last_frame_url TEXT,
    video_width INTEGER,
    video_height INTEGER,
    status VARCHAR(20) DEFAULT 'processing',  -- processing, completed, failed
    progress INTEGER DEFAULT 0,
    cost DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    error_code VARCHAR(50)
);
```

---

# Status Flow

```
Client Request
    ↓
POST /api/video/generate
    ↓
Database: status = 'processing', progress = 0
    ↓
Background Task Starts Polling
    ↓
[Every 30 seconds]
    ↓
GET /api/v1/task/{task_id}
    ↓
Database: Update status/progress
    ↓
Client Polls GET /api/video/status/{id}
    ↓
When completed: status = 'completed', progress = 100
    ↓
Video URL available in library
```

---

# Testing the Workflow

## Test Text-to-Video

```bash
curl -X POST http://localhost:8000/api/video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "123",
    "generation_mode": "text_to_video",
    "script": "A cat playing with a ball",
    "style": "social",
    "duration": 5,
    "aspect_ratio": "16:9"
  }'
```

**Expected Response:**
```json
{
  "video_id": "1",
  "status": "processing",
  "duration": 5,
  "cost": 0.03,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Check Status

```bash
curl http://localhost:8000/api/video/status/1
```

**Response (while processing):**
```json
{
  "video_id": "1",
  "status": "processing",
  "progress": 0
}
```

**Response (when completed):**
```json
{
  "video_id": "1",
  "status": "completed",
  "video_url": "https://...",
  "thumbnail_url": "https://...",
  "progress": 100
}
```

## View in Library

```bash
curl http://localhost:8000/api/video/library?page=1&per_page=20
```

---

# Summary

**Text-to-Video:**
1. User provides script and style
2. Backend generates prompt with style context
3. Sends to PiAPI with `txt2video` task type
4. Receives task_id
5. Saves to database
6. Background task polls for completion
7. Video displayed in library when done

**Image-to-Video:**
1. User provides image URL, script, and style
2. Backend generates prompt with style context
3. Sends to PiAPI with `img2video` task type (includes image)
4. Receives task_id
5. Saves to database
6. Background task polls for completion
7. Animated video displayed in library when done

Both processes follow the same architectural pattern:
- Request → Selection → Service → PiAPI → Database → Polling → Display
