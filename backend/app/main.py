"""
Main FastAPI application for LLM Council.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import chat, models, individual

# Create FastAPI app
app = FastAPI(
    title="LLM Council API",
    description="Backend API for the LLM Council application",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(individual.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LLM Council API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
