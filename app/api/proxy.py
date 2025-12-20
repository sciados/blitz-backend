from fastapi import APIRouter, Query, Response, HTTPException
import httpx
import logging

logger = logging.getLogger(__name__)

# Separate router for proxy - no auth dependencies at all
proxy_router = APIRouter(prefix="", tags=["proxy"])

@proxy_router.get("/api/images/proxy")
async def proxy_image(
    url: str = Query(..., description="Image URL to proxy")
):
    """
    Proxy an image through the backend to add CORS headers.
    
    This is a standalone endpoint with NO authentication.
    Images are already secured through R2 bucket permissions.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/png")

            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=31536000",
                }
            )
    except httpx.HTTPError as e:
        logger.error(f"Failed to proxy image: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to load image: {str(e)}")
    except Exception as e:
        logger.error(f"Image proxy failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image proxy failed: {str(e)}")
