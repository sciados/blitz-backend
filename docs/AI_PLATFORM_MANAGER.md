# AI Platform Manager

## Overview

The AI Platform Manager is a **centralized system for managing AI platform rotation and fallback** across all AI operations in Blitz. It provides a unified interface for selecting, using, and falling back between different AI providers (Stability AI, Replicate, FAL, etc.).

## Benefits

✅ **Single Source of Truth**: All AI platform logic in one place
✅ **Automatic Fallback**: Seamlessly switches platforms when one fails
✅ **Credit-Agnostic**: Works regardless of which platforms have credits
✅ **Health Tracking**: Monitors platform performance and marks unhealthy providers
✅ **Consistent Logging**: All platform switches are logged for monitoring
✅ **Easy to Extend**: Add new platforms without changing existing code

## How It Works

### Platform Priorities

Each operation type has a priority list:

```python
PLATFORM_PRIORITIES = {
    "image_generation": [
        ("pollinations", "free"),       # Free, no API key
        ("huggingface", "free"),        # Free, no API key
        ("fal", "fal-3d"),              # Fast, low cost
        ("flux_pro", "flux-schnell"),   # Good quality/price
        ("stability", "sd-3.5-large"),  # High quality
        ("replicate", "flux"),          # Fallback
    ],
    "image_editing": [
        ("stability", "sd-3.5-large"),  # Primary - best quality
        ("replicate", "flux"),          # Fallback 1
        ("fal", "fal-3d"),              # Fallback 2
    ],
    "text_generation": [
        ("groq", "llama-3.3-70b-versatile"),  # Free, fast
        ("xai", "grok-beta"),                  # Free, fast
        ("google", "gemini-2.5-flash-lite"),   # Cheap, good
        ("together", "llama-3.2-3b-instruct-turbo"),  # Cheap
        ("openai", "gpt-4o-mini"),             # Quality
        ("anthropic", "claude-3-haiku-20240307"),  # Quality
    ],
}
```

### Health Tracking

The manager tracks platform health:
- **Consecutive Failures**: After 3 failures, platform is marked unhealthy
- **Cache TTL**: Unhealthy platforms are skipped for 5 minutes (configurable)
- **Auto-Recovery**: Platforms automatically become healthy after cache expires
- **Response Times**: Tracks average response time per platform

### Credit Handling

Special handling for credit exhaustion:
- Detects "credit", "quota", "billing" errors
- Marks platform as temporarily unhealthy
- Tries next platform in rotation
- **Does NOT permanently blacklist** - allows retry after brief cooldown

## Usage Examples

### 1. Simple Usage with Automatic Fallback

```python
from app.services.ai_platform_manager import ai_platform_manager

# Get best platform for image editing
platform = await ai_platform_manager.get_platform("image_editing")

# Use the platform
if platform.name == "stability":
    service = StabilityAIService()
    result = await service.erase_objects(image_data, mask_data)
elif platform.name == "replicate":
    service = ReplicateService()
    result = await service.erase_objects(image_data, mask_data)
```

### 2. Using with_fallback (Recommended)

```python
from app.services.ai_platform_manager import ai_platform_manager

# Define your operation
def edit_operation(platform, image_data, **params):
    if platform.name == "stability":
        service = StabilityAIService()
        return service.erase_objects(image_data, **params)
    elif platform.name == "replicate":
        service = ReplicateService()
        return service.erase_objects(image_data, **params)

# Execute with automatic fallback
result, platform = await ai_platform_manager.with_fallback(
    operation_type="image_editing",
    operation_func=edit_operation,
    image_data=original_image,
    mask_data=mask_data,
    seed=42
)

print(f"✅ Success using {platform.name}")
```

### 3. Image Generator Integration

```python
from app.services.ai_platform_manager import ai_platform_manager

class ImageGenerator:
    async def generate(self, prompt, style):
        # Get platform from manager
        platform = await ai_platform_manager.get_platform(
            "image_generation",
            quality_boost=True
        )

        # Use platform
        if platform.name == "flux_pro":
            return await self.generate_with_flux(prompt, style)
        elif platform.name == "stability":
            return await self.generate_with_stability(prompt, style)
        # etc.

        # Report success/failure
        try:
            result = await generate()
            await ai_platform_manager.report_success(platform, "image_generation")
            return result
        except Exception as e:
            await ai_platform_manager.report_failure(platform, "image_generation", e)
            raise
```

## API Reference

### `ai_platform_manager.get_platform(operation_type, **kwargs)`

Get the best available platform for an operation type.

**Parameters:**
- `operation_type`: One of "image_generation", "image_editing", "text_generation", "video_generation"
- `attempt`: Current attempt number (internal use)
- `max_attempts`: Maximum fallback attempts (default: 5)
- `**kwargs`: Additional context

**Returns:** `PlatformSpec` object with:
- `name`: Platform name ("stability", "replicate", etc.)
- `model`: Specific model name
- `operation_types`: Supported operation types
- `priority`: Priority level (0 = highest)
- `estimated_cost`: Estimated cost per operation
- `estimated_time`: Estimated time per operation
- `api_key_env`: Environment variable for API key

**Raises:** `RuntimeError` if all platforms fail

### `ai_platform_manager.with_fallback(operation_type, operation_func, *args, **kwargs)`

Execute an operation with automatic fallback to next platform.

**Parameters:**
- `operation_type`: Type of operation
- `operation_func`: Callable that takes platform and returns result
- `*args, **kwargs`: Arguments for operation_func

**Returns:** Tuple of `(result, platform_used)`

**Raises:** `RuntimeError` if all platforms fail

### `ai_platform_manager.report_success(platform, operation_type, response_time=None)`

Report successful operation on a platform.

### `ai_platform_manager.report_failure(platform, operation_type, error, response_time=None)`

Report failed operation on a platform.

### `ai_platform_manager.get_health_status()`

Get health status for all platforms.

**Returns:** Dictionary with platform health metrics:
```python
{
    "stability": {
        "is_healthy": True,
        "consecutive_failures": 0,
        "total_requests": 100,
        "failure_rate": 0.02,
        "avg_response_time": 4.5,
        "last_success": "2025-01-01T12:00:00",
        "last_failure": None,
    },
    # ... other platforms
}
```

## Configuration

### Environment Variables

Platform manager uses settings from `settings.py`:

```python
AI_FALLBACK_ENABLED: bool = True      # Enable automatic fallback
AI_CACHE_TTL_SECONDS: int = 300       # Cache unhealthy platforms for 5 minutes
AI_COST_OPTIMIZATION: bool = True     # Prioritize cheaper providers
AI_MONITORING_ENABLED: bool = True    # Track platform performance
```

### Adding New Platforms

1. **Add to priorities** in `ai_platform_manager.py`:

```python
PLATFORM_PRIORITIES = {
    "image_editing": [
        ("stability", "sd-3.5-large"),
        ("new_platform", "new_model"),  # Add here
        ("replicate", "flux"),
    ],
}
```

2. **Add cost/time estimates**:

```python
def _get_estimated_cost(self, platform_name: str, operation_type: str) -> float:
    cost_map = {
        "stability": 0.001,
        "new_platform": 0.0005,  # Add here
        "replicate": 0.002,
    }
    return cost_map.get(platform_name, 0.0)
```

3. **Add API key mapping**:

```python
def _get_api_key_env(self, platform_name: str) -> Optional[str]:
    env_map = {
        "stability": "STABILITY_API_KEY",
        "new_platform": "NEW_PLATFORM_API_KEY",  # Add here
        "replicate": "REPLICATE_API_TOKEN",
    }
    return env_map.get(platform_name)
```

4. **Update operation handlers** in your service code:

```python
def _execute_with_platform(platform, image_data, **params):
    if platform.name == "stability":
        service = StabilityAIService()
        return service.operation(image_data, **params)
    elif platform.name == "new_platform":  # Add handler
        service = NewPlatformService()
        return service.operation(image_data, **params)
    # ...
```

## Monitoring

### Health Dashboard

Get platform health status:

```python
from app.services.ai_platform_manager import ai_platform_manager

status = ai_platform_manager.get_health_status()
for platform, health in status.items():
    print(f"{platform}: {'✅' if health['is_healthy'] else '❌'} "
          f"({health['consecutive_failures']} failures)")
```

### Logging

All platform operations are logged:

```
✅ Image editing completed using stability
⚠️ Skipping unhealthy platform: stability
🎯 Selected platform for image_editing: stability (sd-3.5-large)
💳 Platform stability has credit issues: Stability has No Credits
🚫 Marking stability as unhealthy after 3 failures
✅ Image editing completed using replicate
```

## Best Practices

1. **Always use `with_fallback`** for new operations - it handles everything automatically
2. **Report success/failure** after each operation to maintain accurate health metrics
3. **Don't hardcode platforms** - always ask the manager for the best platform
4. **Monitor health status** regularly to detect issues early
5. **Handle credit exhaustion gracefully** - the manager will automatically try next platform

## Troubleshooting

### "All platforms failed for operation"

**Causes:**
- All platforms are temporarily unhealthy
- Network issues
- API key problems

**Solutions:**
1. Check platform health status
2. Verify API keys are set
3. Check network connectivity
4. Try again after 5 minutes (cache expires)

### Platform never used

**Causes:**
- Platform marked unhealthy
- Platform not in priority list for operation type
- Higher priority platforms always succeed

**Solutions:**
1. Check health status: `ai_platform_manager.get_health_status()`
2. Review platform priorities in `PLATFORM_PRIORITIES`
3. Manually reset health cache if needed

### Credit exhaustion errors

**The manager handles this automatically:**
1. Detects credit errors
2. Marks platform temporarily unhealthy
3. Tries next platform in rotation
4. Allows retry after cache expires (5 min)

No manual intervention needed!

## Migration Guide

### From Direct Platform Calls

**Before:**
```python
service = StabilityAIService()
result = await service.erase_objects(image_data, mask_data)
```

**After:**
```python
# Simple - just wrap in with_fallback
def operation(platform, image_data, **params):
    service = StabilityAIService()
    return service.erase_objects(image_data, **params)

result, platform = await ai_platform_manager.with_fallback(
    "image_editing", operation, image_data=image_data, mask_data=mask_data
)
```

### From Custom Rotation Logic

**Before:**
```python
self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
provider = self.providers[self.current_provider_index]
```

**After:**
```python
platform = await ai_platform_manager.get_platform("image_editing")
```

Much simpler!

## Future Enhancements

- [ ] Add cost tracking per platform
- [ ] Add response time monitoring
- [ ] Add priority adjustment based on usage
- [ ] Add platform-specific error handling
- [ ] Add automatic platform discovery
- [ ] Add performance metrics dashboard

## Support

For issues or questions about the AI Platform Manager:
1. Check logs for platform switch messages
2. Verify API keys are set correctly
3. Check platform health status
4. Review this documentation
