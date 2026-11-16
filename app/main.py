from fastapi import FastAPI
from app.config import settings
from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import PostingService

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automated Multi-Platform Posting System API"
)

posting_service = PostingService()


@app.get("/")
def read_root():
    return {
        "message": "Automated Multi-Platform Posting System is running",
        "docs_url": "/docs"
    }


@app.get("/health")
def read_health():
    return {"status": "healthy"}


@app.post("/posting", response_model=PostingResponse)
async def post_message(payload: PostingRequest):
    """Publish a validated message across all configured platforms."""
    return await posting_service.post_to_all(payload.message)
