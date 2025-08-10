# PRP: Fraud Banker Chatbot System

## Feature Overview
Build a comprehensive fraud detection chatbot system that enables bankers to:
1. Input customer IDs to retrieve transaction data from Excel files
2. Generate AI-powered transaction summaries using OpenAI API
3. Receive 5-8 investigative questions for customer interviews
4. Interact through a web-based chat interface

**Reference UI**: https://fraud-chatbot-32cw.onrender.com/chat

## Critical Context & Research

### Architecture Patterns from Research
- **FastAPI Framework**: Chosen for high performance, automatic API docs, and excellent ML integration
- **Data Processing**: pandas + openpyxl for Excel handling with efficient data manipulation
- **AI Integration**: OpenAI Chat Completions API for transaction summaries and question generation
- **Frontend**: Clean chat interface with gradient background, real-time messaging, loading states

### Key Technical References
- **FastAPI + Excel Integration**: https://medium.com/@liamwr17/supercharge-your-apis-with-csv-and-excel-exports-fastapi-pandas-a371b2c8f030
- **FastAPI + OpenAI Integration**: https://medium.com/@reddyyashu20/beginners-guide-to-fastapi-openai-chatgpt-api-integration-50a0c3b8571e
- **Fraud Detection Best Practices**: https://dev.to/ekemini_thompson/building-a-real-time-credit-card-fraud-detection-system-with-fastapi-and-machine-learning-3g0m
- **Chatbot UI Patterns**: https://codesignal.com/learn/paths/building-a-chatbot-with-fastapi-and-openai

### Fraud Investigation Question Patterns (Research-Based)
From fraud analyst interview research, key investigative areas include:
- **Transaction Patterns**: Unusual volumes, frequencies, amounts, geographic anomalies
- **Account Activity**: Device changes, IP location shifts, velocity checks
- **Customer Behavior**: Deviation from historical patterns, timing anomalies
- **Risk Indicators**: Cross-referencing multiple data sources, identity verification

## Implementation Blueprint

### Pseudocode Approach
```python
# Core Flow
1. Banker inputs customer_id via chat interface
2. FastAPI endpoint /analyze-customer/{customer_id}
3. Load Excel data using pandas.read_excel()
4. Filter transactions by customer_id
5. Format transaction data for OpenAI API
6. Send to OpenAI with fraud-analysis prompt
7. Parse response for summary + questions
8. Return structured response to frontend
9. Display results in chat interface
```

### Data Flow Architecture
```
Frontend (Chat UI) 
    ↓ POST /analyze-customer
FastAPI Backend
    ↓ pandas.read_excel()
Excel Data Processing
    ↓ Filtered customer data
OpenAI API Integration
    ↓ Summary + Questions
Response Formatting
    ↓ JSON Response
Chat Interface Display
```

## File Structure Implementation

```
fraud_investment_banker_chatbot/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Dependencies
├── .env                        # Environment variables (OpenAI key)
├── src/
│   ├── __init__.py
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── customer.py        # Customer data models
│   │   └── analysis.py        # Analysis response models
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── data_service.py    # Excel data processing
│   │   ├── ai_service.py      # OpenAI integration
│   │   └── analysis_service.py # Transaction analysis
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   └── analysis.py        # Analysis endpoints
│   └── utils/                 # Helper functions
│       ├── __init__.py
│       └── excel_utils.py     # Excel processing utilities
├── static/                    # Frontend files
│   ├── index.html            # Main chat interface
│   ├── style.css             # UI styling
│   └── script.js             # Chat functionality
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_data_service.py
│   ├── test_ai_service.py
│   └── test_analysis_service.py
└── data/
    └── fraud_data.xlsx       # Transaction data
```

## Critical Implementation Details

### Excel Data Processing Pattern
```python
# Based on FastAPI + pandas best practices
import pandas as pd
from io import BytesIO

def load_customer_transactions(customer_id: str) -> pd.DataFrame:
    """Load and filter customer transaction data."""
    df = pd.read_excel("data/fraud_data.xlsx")
    customer_data = df[df['customer_id'] == customer_id]
    return customer_data

def format_for_ai_analysis(df: pd.DataFrame) -> str:
    """Format transaction data for OpenAI analysis."""
    # Convert to structured text for AI processing
    transaction_summary = df.to_string(index=False)
    return transaction_summary
```

### OpenAI Integration Pattern
```python
# Based on OpenAI + FastAPI integration research
import openai
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    customer_id: str

class AnalysisResponse(BaseModel):
    summary: str
    questions: list[str]
    risk_level: str

async def analyze_transactions(transaction_data: str) -> AnalysisResponse:
    """Generate AI-powered fraud analysis."""
    prompt = f"""
    Analyze these banking transactions for potential fraud indicators:
    {transaction_data}
    
    Provide:
    1. A concise summary of transaction patterns
    2. 5-8 specific questions a banker should ask the customer
    3. Risk assessment (Low/Medium/High)
    
    Format as JSON with keys: summary, questions, risk_level
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return parse_ai_response(response.choices[0].message.content)
```

### Frontend Chat Interface Pattern
Based on reference UI analysis (https://fraud-chatbot-32cw.onrender.com/chat):
```javascript
// Key UI components from research
const chatInterface = {
    container: "500px width, 600px height",
    background: "gradient purple-blue",
    messaging: "real-time with loading indicators",
    input: "disabled during processing",
    responses: "formatted with timestamps"
};

// Core functionality
async function analyzeCustomer(customerId) {
    showLoading();
    const response = await fetch(`/analyze-customer/${customerId}`, {
        method: 'POST'
    });
    const analysis = await response.json();
    displayAnalysis(analysis);
    hideLoading();
}
```

## Security & Error Handling

### API Key Management
```python
# Use python-dotenv for secure environment variable handling
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
```

### Input Validation
```python
# Pydantic validation for customer IDs
from pydantic import BaseModel, validator

class CustomerRequest(BaseModel):
    customer_id: str
    
    @validator('customer_id')
    def validate_customer_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Customer ID is required')
        return v.strip()
```

### Error Handling Patterns
```python
# Based on FastAPI best practices
from fastapi import HTTPException

@app.post("/analyze-customer/{customer_id}")
async def analyze_customer(customer_id: str):
    try:
        # Process customer data
        pass
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Customer data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Analysis failed")
```

## Dependencies & Requirements

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.0
openpyxl==3.1.2
openai==1.3.0
python-dotenv==1.0.0
pydantic==2.4.0
pytest==7.4.0
httpx==0.25.0
```

## Implementation Tasks (Sequential Order)

### Phase 1: Project Setup
1. **Initialize project structure** - Create directory hierarchy and core files
2. **Setup virtual environment** - Create venv_linux and install dependencies
3. **Environment configuration** - Setup .env with OpenAI API key
4. **Basic FastAPI setup** - Create main.py with basic FastAPI app

### Phase 2: Data Processing Layer
5. **Excel data service** - Implement data_service.py with pandas integration
6. **Customer data models** - Create Pydantic models for data validation
7. **Data processing tests** - Unit tests for Excel reading and filtering
8. **Excel utilities** - Helper functions for data manipulation

### Phase 3: AI Integration Layer  
9. **OpenAI service setup** - Implement ai_service.py with OpenAI client
10. **Fraud analysis prompts** - Design prompts for transaction summaries
11. **Question generation** - Implement banker question generation logic
12. **AI service tests** - Unit tests for OpenAI integration

### Phase 4: API Layer
13. **Analysis endpoints** - Create FastAPI endpoints for customer analysis
14. **Response models** - Pydantic models for API responses
15. **Error handling** - Comprehensive error handling and validation
16. **API documentation** - FastAPI automatic docs configuration

### Phase 5: Frontend Layer
17. **Chat interface HTML** - Create index.html based on reference UI
18. **CSS styling** - Implement gradient background and chat styling
19. **JavaScript functionality** - Real-time chat with loading states
20. **Frontend-backend integration** - Connect chat to FastAPI endpoints

### Phase 6: Testing & Validation
21. **Unit test suite** - Complete pytest test coverage
22. **Integration testing** - End-to-end workflow testing
23. **Error scenario testing** - Test edge cases and error handling
24. **Performance testing** - Validate response times and load handling

## Validation Gates (Executable)

### Code Quality & Style
```bash
# Install development dependencies
pip install ruff mypy black

# Format and lint
black src/ tests/
ruff check --fix src/ tests/
mypy src/ tests/
```

### Testing Suite
```bash
# Run complete test suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test categories  
pytest tests/test_data_service.py -v
pytest tests/test_ai_service.py -v
pytest tests/test_analysis_service.py -v
```

### Application Validation
```bash
# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test API endpoints
curl -X POST "http://localhost:8000/analyze-customer/12345"

# Access API documentation
open http://localhost:8000/docs
```

### Data Validation
```bash
# Test Excel data processing
python -c "
import pandas as pd
df = pd.read_excel('data/fraud_data.xlsx')
print(f'Data loaded: {df.shape[0]} rows, {df.shape[1]} columns')
print('Columns:', list(df.columns))
"
```

## Gotchas & Common Pitfalls

### Excel Processing Issues
- **Encoding Problems**: Use `encoding='utf-8'` when reading Excel files
- **Memory Usage**: For large Excel files, consider chunking with `chunksize` parameter
- **Data Types**: Explicitly define dtypes to prevent pandas type inference issues

### OpenAI API Considerations
- **Rate Limiting**: Implement exponential backoff for API calls
- **Token Limits**: Monitor token usage, especially with large transaction datasets
- **Cost Management**: Track API usage to avoid unexpected costs
- **Response Parsing**: Handle malformed JSON responses from OpenAI

### FastAPI Specific
- **CORS Issues**: Configure CORS for frontend-backend communication
- **Static Files**: Use StaticFiles mount for serving frontend assets
- **Environment Variables**: Never commit .env files to version control

### Fraud Detection Patterns
- **Question Quality**: Ensure questions are specific, actionable, and follow banking compliance
- **Risk Assessment**: Implement consistent risk scoring methodology
- **Data Privacy**: Mask sensitive customer information in logs

## Success Metrics

### Technical Performance
- API response time < 3 seconds for customer analysis
- 99% uptime for critical endpoints
- Zero data processing errors for valid customer IDs

### Functional Requirements
- Successfully process customer transactions from Excel
- Generate relevant fraud investigation questions
- Provide accurate transaction summaries
- Handle error cases gracefully

### User Experience
- Intuitive chat interface matching reference design
- Real-time feedback with loading states
- Clear error messages for invalid inputs

## PRP Confidence Score: 9/10

**Rationale**: This PRP provides comprehensive context with:
- Complete architectural guidance based on industry best practices
- Specific code patterns from research
- Sequential implementation tasks
- Executable validation gates
- Detailed error handling and gotchas
- External documentation references
- Clear success metrics

**Potential Risk Areas**: 
- Excel data structure unknown (mitigated by flexible pandas approach)
- OpenAI API response formatting variations (mitigated by robust parsing)

The high confidence score reflects thorough research, proven architectural patterns, and comprehensive implementation guidance that should enable one-pass success.