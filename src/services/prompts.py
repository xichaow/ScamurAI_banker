"""
Fraud Analysis Prompts

This module contains expertly crafted prompts for fraud detection analysis,
based on banking industry best practices and fraud investigation techniques.
"""

from typing import Dict, Any
from enum import Enum

class PromptType(str, Enum):
    """Types of analysis prompts."""
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    QUICK_ASSESSMENT = "quick_assessment"
    FOLLOW_UP = "follow_up"
    RISK_SCORING = "risk_scoring"

class FraudAnalysisPrompts:
    """Collection of fraud analysis prompts based on industry best practices."""
    
    @staticmethod
    def get_system_prompt(analysis_type: PromptType = PromptType.COMPREHENSIVE_ANALYSIS) -> str:
        """
        Get system prompt for fraud analysis.
        
        Args:
            analysis_type (PromptType): Type of analysis to perform
            
        Returns:
            str: System prompt
        """
        base_expertise = """
        You are a senior fraud analyst with 15+ years of experience in banking fraud detection.
        You specialize in analyzing customer transaction patterns, risk indicators, and generating
        actionable investigative questions for banking professionals.
        
        Your expertise includes:
        - Transaction pattern analysis and anomaly detection
        - Risk assessment using multiple fraud indicators
        - Identity verification and account security analysis
        - Behavioral pattern recognition
        - Regulatory compliance and investigation protocols
        """
        
        if analysis_type == PromptType.COMPREHENSIVE_ANALYSIS:
            return base_expertise + """
            
            TASK: Perform comprehensive fraud risk analysis
            
            Analyze the provided customer data thoroughly and generate:
            1. SUMMARY: Detailed analysis of fraud indicators and risk factors (2-3 paragraphs)
            2. QUESTIONS: 5 specific scam investigation questions for fraud analyst customer calls
            3. RISK_LEVEL: Assessment (Low/Medium/High) with confidence reasoning
            
            QUESTION GUIDELINES:
            - Focus on scam investigation and fraud prevention
            - Ask about investment scams, remote access, and payment patterns
            - Investigate customer awareness and scammer contact methods
            - Check for multiple payments, future transactions, and customer resistance
            - Professional but direct questions to uncover fraud schemes
            
            RISK ASSESSMENT FACTORS:
            - Multiple high-risk flags = Higher concern
            - Recent fraud history = Immediate attention
            - Unusual transaction patterns = Investigation required
            - Account access anomalies = Security review needed
            
            Format response as valid JSON with keys: summary, questions, risk_level
            """
        
        elif analysis_type == PromptType.QUICK_ASSESSMENT:
            return base_expertise + """
            
            TASK: Quick fraud risk assessment
            
            Provide rapid assessment focusing on immediate red flags and priority actions.
            Generate concise summary and 3-5 critical questions for immediate banker action.
            
            Format response as valid JSON with keys: summary, questions, risk_level
            """
        
        elif analysis_type == PromptType.FOLLOW_UP:
            return base_expertise + """
            
            TASK: Generate follow-up questions
            
            Based on previous analysis and conversation context, generate 3-5 targeted
            follow-up questions to gather additional information or clarify concerns.
            
            Return JSON array of specific follow-up questions.
            """
        
        else:  # RISK_SCORING
            return base_expertise + """
            
            TASK: Risk scoring and prioritization
            
            Evaluate multiple risk factors and provide detailed scoring rationale.
            Focus on quantitative assessment and comparative risk levels.
            
            Format response as JSON with risk_score (0-100), risk_factors, and recommendations.
            """
    
    @staticmethod
    def get_comprehensive_analysis_prompt(
        customer_id: str, 
        transaction_data: str,
        context: str = ""
    ) -> str:
        """
        Generate comprehensive fraud analysis prompt.
        
        Args:
            customer_id (str): Customer identifier
            transaction_data (str): Formatted transaction data
            context (str): Additional context
            
        Returns:
            str: Complete analysis prompt
        """
        return f"""
        CUSTOMER FRAUD ANALYSIS REQUEST
        
        Customer ID: {customer_id}
        
        TRANSACTION DATA AND RISK INDICATORS:
        {transaction_data}
        
        {f"ADDITIONAL CONTEXT: {context}" if context else ""}
        
        ANALYSIS REQUIREMENTS:
        
        1. FRAUD INDICATOR ASSESSMENT:
           - Evaluate BioCatch, Group IB, SASFM, and ISOD risk flags
           - Analyze fraud case history (past 30 days)
           - Identify patterns suggesting account compromise or unauthorized access
           - Consider transaction velocity, amounts, and timing anomalies
        
        2. RISK FACTOR EVALUATION:
           - Multiple high-risk flags: Immediate concern
           - Recent fraud cases: Historical context  
           - Account access patterns: Device/location analysis
           - Behavioral indicators: Deviation from normal patterns
           
           Note: Analysis may reference internal systems (BioCatch, GroupIB, SASFM, ISOD) but 
           questions for customers must use plain language only.
        
        3. INVESTIGATIVE QUESTIONS (exactly 5 questions):
           CRITICAL: Generate ONLY these 5 question types in customer-friendly language:
           1. "Do you believe you are investing with a real firm?"
           2. "Was the contact initiated by you or did they contact you first?"
           3. "Is there any remote access to your computer or are you currently on a call with them?"
           4. "Are there multiple payments set up or any future dated payments?"
           5. "Are you hesitant to believe this might be a scam?"
           
           STRICTLY FORBIDDEN - NEVER mention these in questions:
           - BioCatch, Group IB, SASFM, ISOD
           - "High-risk flags", "medium-risk flags", "low-risk flags"  
           - Any internal banking system names
           - Technical risk assessment terminology
           
           Questions must be conversational and suitable for customer phone calls.
           
        QUESTION FORMATTING GUIDELINES:
        - Use professional, non-accusatory language
        - Be specific with dates, amounts, or transaction details when possible
        - Focus on verification rather than confrontation
        - Include context for why you're asking each question
        
        4. RISK LEVEL DETERMINATION:
           - LOW: Single minor risk flag, no fraud history, explainable patterns
           - MEDIUM: Multiple flags OR recent fraud history OR unusual patterns requiring attention
           - HIGH: Multiple high-risk flags AND/OR recent fraud cases AND/OR clear suspicious patterns
        
        Respond in valid JSON format:
        {{
            "summary": "Detailed analysis of key findings and risk factors...",
            "questions": [
                "Do you believe you are investing with a real firm?",
                "Was the contact initiated by you or did they contact you first?",
                "Is there any remote access to your computer or are you currently on a call with them?", 
                "Are there multiple payments set up or any future dated payments?",
                "Are you hesitant to believe this might be a scam?"
            ],
            "risk_level": "Low|Medium|High"
        }}
        
        REMEMBER: Questions are for customer calls - NO technical banking terms allowed!
        """
    
    @staticmethod
    def get_transaction_pattern_prompt(transaction_data: str, customer_id: str) -> str:
        """
        Generate prompt focused on transaction pattern analysis.
        
        Args:
            transaction_data (str): Transaction data
            customer_id (str): Customer ID
            
        Returns:
            str: Transaction pattern analysis prompt
        """
        return f"""
        TRANSACTION PATTERN ANALYSIS
        
        Customer: {customer_id}
        Data: {transaction_data}
        
        Focus on identifying:
        1. Unusual transaction volumes or frequencies
        2. Geographic location anomalies 
        3. Time-based patterns (unusual hours/days)
        4. Amount patterns (round numbers, specific ranges)
        5. Velocity patterns (rapid successive transactions)
        
        Generate 5 specific questions about transaction patterns for banker verification.
        
        Return JSON: {{"questions": [...], "pattern_analysis": "...", "risk_level": "..."}}
        """
    
    @staticmethod
    def get_account_security_prompt(risk_flags: Dict[str, Any], customer_id: str) -> str:
        """
        Generate prompt focused on account security concerns.
        
        Args:
            risk_flags (dict): Risk flag data
            customer_id (str): Customer ID
            
        Returns:
            str: Account security analysis prompt
        """
        return f"""
        ACCOUNT SECURITY ANALYSIS
        
        Customer: {customer_id}
        Risk Flags: {risk_flags}
        
        Analyze security indicators:
        1. Device fingerprinting anomalies (BioCatch)
        2. Login pattern irregularities
        3. IP location discrepancies
        4. Access velocity concerns
        5. Authentication bypass attempts
        
        Generate 6-8 security-focused questions for customer verification:
        - Recent device changes
        - Location verification
        - Authentication method changes
        - Suspicious communications received
        - Password/PIN sharing concerns
        
        Return JSON with security_assessment and verification_questions.
        """
    
    @staticmethod
    def get_behavioral_analysis_prompt(customer_data: str, fraud_history: int) -> str:
        """
        Generate prompt for behavioral pattern analysis.
        
        Args:
            customer_data (str): Customer transaction data
            fraud_history (int): Number of fraud cases in past 30 days
            
        Returns:
            str: Behavioral analysis prompt
        """
        return f"""
        BEHAVIORAL PATTERN ANALYSIS
        
        Customer Data: {customer_data}
        Fraud History: {fraud_history} cases in past 30 days
        
        Behavioral Analysis Focus:
        1. Deviation from established patterns
        2. Sudden changes in banking behavior
        3. Inconsistent transaction patterns
        4. Unusual account access patterns
        5. Communication pattern changes
        
        Generate questions to understand:
        - Recent life changes (job, residence, family)
        - Changes in financial needs or circumstances
        - New banking relationships or services
        - Technology usage changes
        - Social or family influences on banking behavior
        
        Provide behavioral_assessment and lifestyle_verification_questions in JSON.
        """
    
    @staticmethod
    def get_follow_up_prompt(
        initial_analysis: str, 
        conversation_context: str,
        customer_id: str
    ) -> str:
        """
        Generate follow-up questions based on conversation context.
        
        Args:
            initial_analysis (str): Previous analysis summary
            conversation_context (str): Current conversation
            customer_id (str): Customer ID
            
        Returns:
            str: Follow-up prompt
        """
        return f"""
        FOLLOW-UP QUESTION GENERATION
        
        Customer: {customer_id}
        
        Previous Analysis: {initial_analysis}
        
        Conversation Context: {conversation_context}
        
        Based on the analysis and conversation, generate 3-5 targeted follow-up questions that:
        1. Clarify any ambiguous responses
        2. Gather additional details about suspicious activities
        3. Verify information provided in conversation
        4. Explore new areas of concern that emerged
        5. Confirm understanding of customer's explanations
        
        Questions should be:
        - Specific to the conversation context
        - Professional and supportive in tone
        - Designed to resolve outstanding concerns
        - Focused on verification and clarification
        
        Return JSON array of follow-up questions with brief context for each.
        """

class QuestionTemplates:
    """Pre-defined question templates for different fraud scenarios."""
    
    TRANSACTION_VERIFICATION = [
        "Can you confirm the transaction of ${amount} on {date} at {merchant}?",
        "Do you recall making a payment to {merchant} on {date}?",
        "Were you expecting any charges from {merchant} around {date}?",
    ]
    
    DEVICE_ACCESS = [
        "Have you accessed your account from any new devices in the past month?",
        "Have you logged into your banking from any public computers or WiFi?",
        "Has anyone else used your device to access banking services?",
    ]
    
    LOCATION_VERIFICATION = [
        "Have you traveled outside your usual area recently?",
        "Are you currently in {location} or have you been there recently?",
        "Have you made any transactions while traveling?",
    ]
    
    SECURITY_CONCERNS = [
        "Have you received any suspicious emails or text messages recently?",
        "Has anyone contacted you claiming to be from the bank?",
        "Have you shared your login credentials with anyone recently?",
    ]
    
    BEHAVIORAL_CHANGES = [
        "Have there been any changes in your financial circumstances recently?",
        "Are you using any new banking services or features?",
        "Has your banking routine changed in any way?",
    ]
    
    IDENTITY_VERIFICATION = [
        "Can you confirm your current contact information is up to date?",
        "Have you moved or changed your address recently?",
        "Are you the only person authorized to use this account?",
    ]

# Helper functions
def get_prompt_for_risk_level(risk_level: str) -> PromptType:
    """
    Get appropriate prompt type based on risk level.
    
    Args:
        risk_level (str): Risk level assessment
        
    Returns:
        PromptType: Appropriate prompt type
    """
    if risk_level.lower() == "high":
        return PromptType.COMPREHENSIVE_ANALYSIS
    elif risk_level.lower() == "medium":
        return PromptType.COMPREHENSIVE_ANALYSIS
    else:
        return PromptType.QUICK_ASSESSMENT

def format_questions_with_context(questions: list, customer_data: Dict[str, Any]) -> list:
    """
    Format questions with customer-specific context.
    
    Args:
        questions (list): Base questions
        customer_data (dict): Customer information
        
    Returns:
        list: Formatted questions with context
    """
    formatted_questions = []
    
    for question in questions:
        # Replace placeholders with actual data
        if "{customer_id}" in question and "customer_id" in customer_data:
            question = question.replace("{customer_id}", customer_data["customer_id"])
        
        # Add more context-specific formatting as needed
        formatted_questions.append(question)
    
    return formatted_questions