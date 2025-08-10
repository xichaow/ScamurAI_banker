"""
Analysis Response Models

Pydantic models for fraud analysis responses from OpenAI API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime

class RiskAssessment(str, Enum):
    """Risk assessment levels."""
    LOW = "Low"
    MEDIUM = "Medium" 
    HIGH = "High"
    CRITICAL = "Critical"

class QuestionCategory(str, Enum):
    """Categories for investigative questions."""
    TRANSACTION_PATTERN = "Transaction Pattern"
    ACCOUNT_ACTIVITY = "Account Activity"
    IDENTITY_VERIFICATION = "Identity Verification"
    BEHAVIORAL_ANALYSIS = "Behavioral Analysis"
    TECHNICAL_INDICATORS = "Technical Indicators"

class InvestigativeQuestion(BaseModel):
    """Model for individual investigative questions."""
    question: str = Field(..., description="The question to ask the customer")
    category: QuestionCategory = Field(..., description="Question category")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5, 5 being highest)")
    context: Optional[str] = Field(None, description="Additional context for the question")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "question": "Can you explain the unusual transaction pattern on [date]?",
                "category": "Transaction Pattern",
                "priority": 4,
                "context": "Multiple high-value transactions detected in short time period"
            }
        }

class FraudAnalysisSummary(BaseModel):
    """Summary of fraud analysis results."""
    customer_id: str = Field(..., description="Customer ID analyzed")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    risk_assessment: RiskAssessment = Field(..., description="Overall risk assessment")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment (0-1)")
    key_findings: List[str] = Field(..., description="Key findings from analysis")
    red_flags: List[str] = Field(default_factory=list, description="Identified red flags")
    summary: str = Field(..., description="Detailed analysis summary")
    
    @validator('key_findings')
    def validate_key_findings(cls, v):
        """Ensure at least one key finding is present."""
        if not v or len(v) == 0:
            raise ValueError("At least one key finding must be provided")
        return v

class AnalysisResponse(BaseModel):
    """Complete analysis response model."""
    customer_id: str = Field(..., description="Customer ID")
    analysis_summary: FraudAnalysisSummary = Field(..., description="Analysis summary")
    investigative_questions: List[InvestigativeQuestion] = Field(
        ..., 
        min_items=5, 
        max_items=8,
        description="5-8 investigative questions for banker"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended immediate actions"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Suggested next steps for investigation"
    )
    
    @validator('investigative_questions')
    def validate_question_count(cls, v):
        """Ensure question count is within required range."""
        if len(v) < 5 or len(v) > 8:
            raise ValueError("Must have between 5-8 investigative questions")
        return v
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "customer_id": "23039203",
                "analysis_summary": {
                    "customer_id": "23039203",
                    "risk_assessment": "High",
                    "confidence_score": 0.85,
                    "key_findings": [
                        "Multiple high-risk flags detected",
                        "Previous fraud case in past 30 days"
                    ],
                    "red_flags": ["High BioCatch risk", "High Group IB flag"],
                    "summary": "Customer shows multiple fraud indicators requiring immediate attention."
                },
                "investigative_questions": [
                    {
                        "question": "Can you verify your recent account activity?",
                        "category": "Account Activity",
                        "priority": 5,
                        "context": "Multiple risk flags detected"
                    }
                ],
                "recommended_actions": ["Immediate account review"],
                "next_steps": ["Schedule customer interview"]
            }
        }

class ChatMessage(BaseModel):
    """Chat message model for frontend communication."""
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    is_bot: bool = Field(default=True, description="Whether message is from bot")
    message_type: str = Field(default="text", description="Type of message (text, analysis, error)")

class ChatRequest(BaseModel):
    """Chat request model."""
    customer_id: str = Field(..., description="Customer ID to analyze")
    message: Optional[str] = Field(None, description="Additional context or question")
    
    @validator('customer_id')
    def validate_customer_id(cls, v):
        """Validate customer ID."""
        if not v or not v.strip():
            raise ValueError('Customer ID is required')
        return v.strip()

class ChatResponse(BaseModel):
    """Chat response model."""
    messages: List[ChatMessage] = Field(..., description="Response messages")
    analysis: Optional[AnalysisResponse] = Field(None, description="Analysis results if requested")
    status: str = Field(default="success", description="Response status")
    error: Optional[str] = Field(None, description="Error message if any")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    customer_id: Optional[str] = Field(None, description="Customer ID if applicable")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "error": "Customer not found",
                "error_code": "CUSTOMER_NOT_FOUND", 
                "customer_id": "invalid_id"
            }
        }