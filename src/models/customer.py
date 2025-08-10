"""
Customer Data Models

Pydantic models for customer data validation and serialization.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator, Field
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low risk"
    MEDIUM = "medium risk" 
    HIGH = "high risk"
    UNKNOWN = "N/A"

class AccountDetails(BaseModel):
    """Bank account details model."""
    bsb: str = Field(..., description="Bank State Branch code")
    account: str = Field(..., description="Account number")

class RiskFlags(BaseModel):
    """Risk assessment flags model."""
    biocatch_flag: str = Field(..., description="BioCatch risk assessment")
    group_ib_flag: str = Field(..., description="Group IB risk assessment")
    sasfm_flag: str = Field(..., description="SASFM risk assessment")
    isod_flag: str = Field(..., description="ISOD risk assessment")

class FraudHistory(BaseModel):
    """Customer fraud history model."""
    cases_past_30_days: int = Field(
        default=0, 
        ge=0,
        description="Number of fraud cases in past 30 days"
    )

class CustomerRequest(BaseModel):
    """Customer analysis request model."""
    customer_id: str = Field(..., description="Customer ID to analyze")
    
    @validator('customer_id')
    def validate_customer_id(cls, v):
        """Validate customer ID format."""
        if not v or not v.strip():
            raise ValueError('Customer ID is required')
        return v.strip()

class CustomerData(BaseModel):
    """Complete customer data model."""
    customer_id: str = Field(..., description="Customer CGID")
    account_details: AccountDetails
    risk_flags: RiskFlags
    fraud_history: FraudHistory
    raw_data: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw transaction data"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "customer_id": "23039203",
                "account_details": {
                    "bsb": "803-323",
                    "account": "123456789"
                },
                "risk_flags": {
                    "biocatch_flag": "high risk",
                    "group_ib_flag": "high risk",
                    "sasfm_flag": "medium risk",
                    "isod_flag": "low risk"
                },
                "fraud_history": {
                    "cases_past_30_days": 1
                },
                "raw_data": []
            }
        }

class CustomerSummary(BaseModel):
    """Customer summary model for quick overview."""
    customer_id: str
    total_risk_flags: int = Field(..., description="Number of high risk flags")
    highest_risk_level: RiskLevel = Field(..., description="Highest risk level found")
    fraud_cases_count: int = Field(..., description="Recent fraud cases count")
    requires_attention: bool = Field(..., description="Whether customer requires immediate attention")
    
    @validator('requires_attention', pre=True, always=True)
    def determine_attention_required(cls, v, values):
        """Determine if customer requires attention based on risk factors."""
        fraud_count = values.get('fraud_cases_count', 0)
        high_risk_flags = values.get('total_risk_flags', 0)
        
        # Customer requires attention if they have fraud cases or multiple high risk flags
        return fraud_count > 0 or high_risk_flags >= 2

class DataInfo(BaseModel):
    """Data source information model."""
    file_path: str = Field(..., description="Path to data file")
    shape: tuple = Field(..., description="Data shape (rows, columns)")
    columns: List[str] = Field(..., description="Available columns")
    total_customers: int = Field(..., description="Total number of customers")
    data_types: Dict[str, str] = Field(..., description="Column data types")

class CustomerListResponse(BaseModel):
    """Response model for customer list."""
    customers: List[str] = Field(..., description="List of available customer IDs")
    total_count: int = Field(..., description="Total number of customers")
    
    @validator('total_count', pre=True, always=True)
    def set_total_count(cls, v, values):
        """Set total count based on customers list length."""
        customers = values.get('customers', [])
        return len(customers)