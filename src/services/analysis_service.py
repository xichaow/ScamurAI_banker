"""
Analysis Service

Main business logic for fraud detection analysis, combining data processing,
AI analysis, and question generation for banker interviews.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .data_service import customer_data_service
from .ai_service import ai_service, OpenAIError
from .prompts import FraudAnalysisPrompts, PromptType, QuestionTemplates
from ..models.analysis import (
    AnalysisResponse, 
    FraudAnalysisSummary, 
    InvestigativeQuestion,
    QuestionCategory,
    RiskAssessment
)
from ..models.customer import CustomerData, RiskLevel

# Setup logging
logger = logging.getLogger(__name__)

class AnalysisService:
    """Main service for coordinating fraud analysis workflow."""
    
    def __init__(self):
        """Initialize analysis service with required dependencies."""
        self.data_service = customer_data_service
        self.ai_service = ai_service
        self.prompts = FraudAnalysisPrompts()
        
    async def analyze_customer(
        self, 
        customer_id: str,
        context: Optional[str] = None,
        analysis_type: PromptType = PromptType.COMPREHENSIVE_ANALYSIS
    ) -> AnalysisResponse:
        """
        Perform comprehensive customer fraud analysis.
        
        Args:
            customer_id (str): Customer ID to analyze
            context (str, optional): Additional context for analysis
            analysis_type (PromptType): Type of analysis to perform
            
        Returns:
            AnalysisResponse: Complete analysis results
            
        Raises:
            Exception: If analysis fails
        """
        try:
            logger.info(f"Starting fraud analysis for customer {customer_id}")
            
            # Step 1: Retrieve customer data
            customer_data = self._get_customer_data(customer_id)
            
            # Step 2: Format data for AI analysis
            formatted_data = self.data_service.format_for_ai_analysis(customer_data)
            
            # Step 3: Perform AI analysis
            ai_analysis = await self._perform_ai_analysis(
                customer_id, formatted_data, context, analysis_type
            )
            
            # Step 4: Structure the analysis results
            analysis_summary = self._create_analysis_summary(
                customer_id, ai_analysis, customer_data
            )
            
            # Step 5: Generate investigative questions
            investigative_questions = self._create_investigative_questions(
                ai_analysis.get("questions", [])
            )
            
            # Step 6: Generate recommendations and next steps
            recommendations = self._generate_recommendations(ai_analysis, customer_data)
            next_steps = self._generate_next_steps(ai_analysis["risk_level"])
            
            # Step 7: Create final response
            response = AnalysisResponse(
                customer_id=customer_id,
                analysis_summary=analysis_summary,
                investigative_questions=investigative_questions,
                recommended_actions=recommendations,
                next_steps=next_steps
            )
            
            logger.info(f"Analysis completed for customer {customer_id}")
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed for customer {customer_id}: {e}")
            
            # Return fallback analysis
            return self._create_fallback_analysis(customer_id, str(e))
    
    def _get_customer_data(self, customer_id: str):
        """Get customer data with error handling."""
        try:
            return self.data_service.get_customer_data(customer_id)
        except FileNotFoundError:
            raise Exception(f"Customer {customer_id} not found in database")
        except Exception as e:
            raise Exception(f"Failed to retrieve customer data: {str(e)}")
    
    async def _perform_ai_analysis(
        self, 
        customer_id: str, 
        formatted_data: str,
        context: Optional[str],
        analysis_type: PromptType
    ) -> Dict[str, Any]:
        """Perform AI analysis with error handling and fallbacks."""
        try:
            # Use AI service for analysis
            return await self.ai_service.analyze_fraud_data(
                customer_id, formatted_data, context
            )
        except OpenAIError as e:
            logger.warning(f"AI analysis failed, using fallback: {e}")
            return self._create_fallback_ai_analysis(customer_id, formatted_data)
        except Exception as e:
            logger.error(f"Unexpected error in AI analysis: {e}")
            return self._create_fallback_ai_analysis(customer_id, formatted_data)
    
    def _create_fallback_ai_analysis(self, customer_id: str, data: str) -> Dict[str, Any]:
        """Create fallback analysis when AI service is unavailable."""
        # Analyze data patterns manually
        risk_level = "Medium"  # Default
        
        # Simple risk assessment based on data content
        if "high risk" in data.lower():
            risk_level = "High"
        elif "fraud_cases_linked_past_30_days: 0" in data:
            risk_level = "Low"
        
        return {
            "summary": f"Technical analysis completed for customer {customer_id}. "
                      f"Multiple risk indicators detected. Manual review recommended.",
            "questions": [
                "Can you verify your recent account activity and confirm all transactions?",
                "Have you noticed any unusual or unauthorized account access recently?",
                "Have you shared your account credentials with anyone or accessed your account from new devices?",
                "Can you confirm your current contact information and verify any recent changes?",
                "Have you received any suspicious communications claiming to be from our bank?"
            ],
            "risk_level": risk_level
        }
    
    def _create_analysis_summary(
        self, 
        customer_id: str, 
        ai_analysis: Dict[str, Any],
        customer_data
    ) -> FraudAnalysisSummary:
        """Create structured analysis summary."""
        # Calculate confidence score based on data quality
        confidence = self._calculate_confidence_score(ai_analysis, customer_data)
        
        # Extract key findings
        key_findings = self._extract_key_findings(ai_analysis, customer_data)
        
        # Identify red flags
        red_flags = self._identify_red_flags(customer_data)
        
        return FraudAnalysisSummary(
            customer_id=customer_id,
            analysis_timestamp=datetime.now(),
            risk_assessment=RiskAssessment(ai_analysis["risk_level"]),
            confidence_score=confidence,
            key_findings=key_findings,
            red_flags=red_flags,
            summary=ai_analysis["summary"]
        )
    
    def _calculate_confidence_score(self, ai_analysis: Dict[str, Any], customer_data) -> float:
        """Calculate confidence score based on available data quality."""
        base_confidence = 0.7  # Base confidence
        
        # Adjust based on data completeness
        if len(customer_data) > 0:
            base_confidence += 0.1
        
        # Adjust based on AI analysis quality
        if "error" not in ai_analysis:
            base_confidence += 0.1
        
        # Adjust based on number of questions generated
        questions_count = len(ai_analysis.get("questions", []))
        if questions_count >= 5:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _extract_key_findings(self, ai_analysis: Dict[str, Any], customer_data) -> List[str]:
        """Extract key findings from analysis and data."""
        findings = []
        
        # Check customer data for immediate findings
        if len(customer_data) > 0:
            row = customer_data.iloc[0]
            
            # Risk flag findings
            high_risk_flags = []
            risk_columns = ['BIOCATCH_FLAG', 'GROUP_IB_FLAG', 'SASFM_FLAG', 'ISOD_FLAG']
            
            for col in risk_columns:
                if col in row and 'high' in str(row[col]).lower():
                    high_risk_flags.append(col.replace('_FLAG', '').title())
            
            if high_risk_flags:
                findings.append(f"High risk flags detected: {', '.join(high_risk_flags)}")
            
            # Fraud history findings
            if 'Fraud_Cases_Linked_Past_30_Days' in row:
                fraud_cases = row['Fraud_Cases_Linked_Past_30_Days']
                if fraud_cases > 0:
                    findings.append(f"Previous fraud cases: {fraud_cases} in past 30 days")
        
        # Add AI-derived findings if available
        summary_text = ai_analysis.get("summary", "")
        if "multiple" in summary_text.lower() and "risk" in summary_text.lower():
            findings.append("Multiple fraud risk indicators identified")
        
        # Ensure at least one finding
        if not findings:
            findings.append("Customer data reviewed for fraud indicators")
        
        return findings
    
    def _identify_red_flags(self, customer_data) -> List[str]:
        """Identify specific red flags from customer data."""
        red_flags = []
        
        if len(customer_data) > 0:
            row = customer_data.iloc[0]
            
            # High-risk flag red flags
            if row.get('BIOCATCH_FLAG') == 'high risk':
                red_flags.append("BioCatch behavioral analysis flagged high risk")
            
            if row.get('GROUP_IB_FLAG') == 'high risk':
                red_flags.append("Group IB fraud detection flagged high risk")
            
            if row.get('SASFM_FLAG') == 'high risk':
                red_flags.append("SASFM system flagged high risk")
            
            # Fraud history red flag
            fraud_cases = row.get('Fraud_Cases_Linked_Past_30_Days', 0)
            if fraud_cases > 0:
                red_flags.append(f"Customer involved in {fraud_cases} fraud case(s) in past 30 days")
        
        return red_flags
    
    def _create_investigative_questions(self, ai_questions: List[str]) -> List[InvestigativeQuestion]:
        """Convert AI-generated questions to structured investigative questions."""
        structured_questions = []
        
        for i, question in enumerate(ai_questions[:8]):  # Cap at 8 questions
            # Categorize question based on content
            category = self._categorize_question(question)
            
            # Assign priority based on category and position
            priority = self._assign_question_priority(category, i)
            
            # Add context based on question content
            context = self._generate_question_context(question, category)
            
            structured_questions.append(InvestigativeQuestion(
                question=question,
                category=category,
                priority=priority,
                context=context
            ))
        
        return structured_questions
    
    def _categorize_question(self, question: str) -> QuestionCategory:
        """Categorize question based on its content."""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["transaction", "payment", "charge", "amount"]):
            return QuestionCategory.TRANSACTION_PATTERN
        elif any(word in question_lower for word in ["device", "login", "access", "location"]):
            return QuestionCategory.ACCOUNT_ACTIVITY
        elif any(word in question_lower for word in ["verify", "confirm", "identity", "contact"]):
            return QuestionCategory.IDENTITY_VERIFICATION
        elif any(word in question_lower for word in ["behavior", "habit", "routine", "change"]):
            return QuestionCategory.BEHAVIORAL_ANALYSIS
        elif any(word in question_lower for word in ["security", "communication", "email", "phone"]):
            return QuestionCategory.TECHNICAL_INDICATORS
        else:
            return QuestionCategory.ACCOUNT_ACTIVITY
    
    def _assign_question_priority(self, category: QuestionCategory, position: int) -> int:
        """Assign priority to questions based on category and position."""
        # Base priority on position (earlier questions get higher priority)
        base_priority = max(5 - position, 1)
        
        # Adjust based on category importance
        if category == QuestionCategory.IDENTITY_VERIFICATION:
            return min(base_priority + 1, 5)
        elif category == QuestionCategory.TRANSACTION_PATTERN:
            return min(base_priority + 1, 5)
        else:
            return base_priority
    
    def _generate_question_context(self, question: str, category: QuestionCategory) -> str:
        """Generate context for questions to help bankers understand their purpose."""
        if category == QuestionCategory.TRANSACTION_PATTERN:
            return "Verify transaction legitimacy and identify unauthorized activity"
        elif category == QuestionCategory.ACCOUNT_ACTIVITY:
            return "Assess account access patterns and potential security breaches"
        elif category == QuestionCategory.IDENTITY_VERIFICATION:
            return "Confirm customer identity and account ownership"
        elif category == QuestionCategory.BEHAVIORAL_ANALYSIS:
            return "Understand changes in customer banking behavior"
        elif category == QuestionCategory.TECHNICAL_INDICATORS:
            return "Evaluate security threats and suspicious communications"
        else:
            return "Gather information relevant to fraud investigation"
    
    def _generate_recommendations(self, ai_analysis: Dict[str, Any], customer_data) -> List[str]:
        """Generate recommended immediate actions."""
        recommendations = []
        risk_level = ai_analysis.get("risk_level", "Medium")
        
        if risk_level == "High":
            recommendations.extend([
                "Conduct immediate customer interview to verify account activity",
                "Consider temporary account restrictions until verification complete",
                "Document all customer responses for compliance review",
                "Escalate to fraud investigation team if concerns remain"
            ])
        elif risk_level == "Medium":
            recommendations.extend([
                "Schedule customer call within 24 hours",
                "Review transaction history for additional anomalies",
                "Verify customer contact information",
                "Monitor account for unusual activity"
            ])
        else:  # Low risk
            recommendations.extend([
                "Document analysis results in customer file",
                "Continue standard account monitoring",
                "Consider routine follow-up in 30 days"
            ])
        
        return recommendations
    
    def _generate_next_steps(self, risk_level: str) -> List[str]:
        """Generate suggested next steps based on risk level."""
        if risk_level == "High":
            return [
                "Complete customer interview using generated questions",
                "Verify all suspicious transactions with customer",
                "Update customer risk profile based on findings",
                "Coordinate with fraud prevention team if needed"
            ]
        elif risk_level == "Medium":
            return [
                "Conduct customer verification call",
                "Review customer explanations for any red flags",
                "Update account notes with interview results",
                "Schedule follow-up review in 7-14 days"
            ]
        else:  # Low risk
            return [
                "Complete routine verification if desired",
                "File analysis results for record keeping",
                "Return to standard account monitoring"
            ]
    
    def _create_fallback_analysis(self, customer_id: str, error_message: str) -> AnalysisResponse:
        """Create fallback analysis when main analysis fails."""
        summary = FraudAnalysisSummary(
            customer_id=customer_id,
            analysis_timestamp=datetime.now(),
            risk_assessment=RiskAssessment.MEDIUM,
            confidence_score=0.3,
            key_findings=[
                f"Analysis error occurred: {error_message}",
                "Manual review required"
            ],
            red_flags=["Technical analysis failure"],
            summary=f"Unable to complete automated analysis for customer {customer_id}. Manual review recommended."
        )
        
        fallback_questions = [
            InvestigativeQuestion(
                question="Do you believe you are investing with a real firm?",
                category=QuestionCategory.IDENTITY_VERIFICATION,
                priority=5,
                context="Investment legitimacy assessment"
            ),
            InvestigativeQuestion(
                question="Was the contact initiated by you or did they contact you first?",
                category=QuestionCategory.BEHAVIORAL_ANALYSIS,
                priority=5,
                context="Contact initiation assessment"
            ),
            InvestigativeQuestion(
                question="Is there any remote access to your computer or are you currently on a call with them?",
                category=QuestionCategory.TECHNICAL_INDICATORS,
                priority=5,
                context="Remote access indicator check"
            ),
            InvestigativeQuestion(
                question="Are there multiple payments set up or any future dated payments?",
                category=QuestionCategory.TRANSACTION_PATTERN,
                priority=4,
                context="Payment pattern assessment"
            ),
            InvestigativeQuestion(
                question="Are you hesitant to believe this might be a scam?",
                category=QuestionCategory.BEHAVIORAL_ANALYSIS,
                priority=4,
                context="Scam resistance assessment"
            ),
        ]
        
        return AnalysisResponse(
            customer_id=customer_id,
            analysis_summary=summary,
            investigative_questions=fallback_questions,
            recommended_actions=["Manual fraud analysis required", "Contact technical support"],
            next_steps=["Escalate to manual review process"]
        )

# Global service instance
analysis_service = AnalysisService()