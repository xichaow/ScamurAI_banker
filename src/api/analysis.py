"""
Analysis API Endpoints

FastAPI endpoints for fraud analysis functionality.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import logging

from ..services.analysis_service import analysis_service
from ..services.data_service import customer_data_service
from ..models.customer import CustomerRequest, CustomerListResponse
from ..models.analysis import AnalysisResponse, ChatRequest, ChatResponse, ChatMessage, ErrorResponse

# Setup logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api", tags=["fraud-analysis"])

@router.get("/customers", response_model=CustomerListResponse)
async def get_available_customers():
    """
    Get list of available customers for analysis.
    
    Returns:
        CustomerListResponse: List of customer IDs
    """
    try:
        customers = customer_data_service.get_available_customers()
        return CustomerListResponse(customers=customers)
    except Exception as e:
        logger.error(f"Failed to get customer list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer list"
        )

@router.post("/analyze/{customer_id}", response_model=AnalysisResponse)
async def analyze_customer(
    customer_id: str,
    context: Optional[str] = None
):
    """
    Analyze customer for fraud indicators.
    
    Args:
        customer_id (str): Customer ID to analyze
        context (str, optional): Additional context for analysis
        
    Returns:
        AnalysisResponse: Complete fraud analysis results
    """
    try:
        logger.info(f"Starting analysis for customer {customer_id}")
        
        # Validate customer exists
        if not customer_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer ID is required"
            )
        
        # Perform analysis
        analysis = await analysis_service.analyze_customer(
            customer_id=customer_id.strip(),
            context=context
        )
        
        logger.info(f"Analysis completed for customer {customer_id}")
        return analysis
        
    except HTTPException:
        raise
    except FileNotFoundError:
        logger.warning(f"Customer {customer_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    except Exception as e:
        logger.error(f"Analysis failed for customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed due to technical error"
        )

@router.get("/customer/{customer_id}/summary")
async def get_customer_summary(customer_id: str):
    """
    Get customer summary information.
    
    Args:
        customer_id (str): Customer ID
        
    Returns:
        dict: Customer summary data
    """
    try:
        if not customer_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer ID is required"
            )
        
        summary = customer_data_service.get_customer_summary(customer_id.strip())
        return summary
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to get customer summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve customer summary"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_analyze(request: ChatRequest):
    """
    Chat-based customer analysis endpoint.
    
    Args:
        request (ChatRequest): Chat analysis request
        
    Returns:
        ChatResponse: Chat response with analysis
    """
    try:
        logger.info(f"Chat analysis request for customer {request.customer_id}")
        
        # Perform analysis
        analysis = await analysis_service.analyze_customer(
            customer_id=request.customer_id,
            context=request.message
        )
        
        # Create chat messages
        messages = [
            ChatMessage(
                message=f"Analysis completed for customer {request.customer_id}",
                is_bot=True,
                message_type="analysis"
            ),
            ChatMessage(
                message=f"Risk Level: {analysis.analysis_summary.risk_assessment}",
                is_bot=True,
                message_type="text"
            )
        ]
        
        # Add key findings
        for finding in analysis.analysis_summary.key_findings:
            messages.append(ChatMessage(
                message=f"• {finding}",
                is_bot=True,
                message_type="text"
            ))
        
        return ChatResponse(
            messages=messages,
            analysis=analysis,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Chat analysis failed: {e}")
        error_message = ChatMessage(
            message=f"Analysis failed: {str(e)}",
            is_bot=True,
            message_type="error"
        )
        
        return ChatResponse(
            messages=[error_message],
            status="error",
            error=str(e)
        )

@router.get("/data/info")
async def get_data_info():
    """
    Get information about the fraud data source.
    
    Returns:
        dict: Data source information
    """
    try:
        info = customer_data_service.get_data_info()
        return info
    except Exception as e:
        logger.error(f"Failed to get data info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data information"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the analysis API.
    
    Returns:
        dict: Health status
    """
    try:
        # Test data service
        data_info = customer_data_service.get_data_info()
        customers_available = len(customer_data_service.get_available_customers())
        
        # Test AI service (basic check)
        from ..services.ai_service import ai_service
        ai_stats = ai_service.get_usage_stats()
        
        return {
            "status": "healthy",
            "data_service": "operational",
            "customers_available": customers_available,
            "ai_service": "configured" if ai_stats["api_configured"] else "not_configured",
            "model": ai_stats["model"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )