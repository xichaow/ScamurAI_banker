"""
Fraud Banker Chatbot - Main FastAPI Application

This application provides a chatbot interface for bankers to analyze
customer transaction data for potential fraud indicators using OpenAI API.
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import API routes
from src.api.analysis import router as analysis_router

# Initialize FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "Fraud Banker Chatbot"),
    description="AI-powered fraud detection chatbot for banking professionals",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(analysis_router)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint - serve the chat interface
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the main chat interface.
    
    Returns:
        HTMLResponse: The chat interface HTML
    """
    try:
        with open("static/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Fraud Banker Chatbot</h1><p>Frontend not yet available</p>",
            status_code=200
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Application health status
    """
    return {
        "status": "healthy",
        "app": os.getenv("APP_NAME", "Fraud Banker Chatbot"),
        "version": "1.0.0"
    }

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🚀 Fraud Banker Chatbot starting up...")
    print(f"📊 Data file: {os.getenv('DATA_FILE_PATH', 'data/fraud_data.xlsx')}")
    
    # Verify OpenAI API key is configured
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("⚠️  Warning: OpenAI API key not configured. Please update .env file.")
    else:
        print("✓ OpenAI API key configured")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )