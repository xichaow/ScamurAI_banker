"""
AI Service for OpenAI Integration

This module handles OpenAI API interactions for fraud analysis,
transaction summaries, and investigative question generation.
"""

import os
import json
import asyncio
import time
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

class OpenAIError(Exception):
    """Custom exception for OpenAI related errors."""
    pass

class OpenAIService:
    """Service for OpenAI API interactions."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI service.
        
        Args:
            api_key (str, optional): OpenAI API key
            model (str): Model to use for completions
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise OpenAIError("OpenAI API key not configured. Please update .env file.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Rate limiting and token tracking
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        self.token_usage = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    
    async def _rate_limit(self):
        """Implement simple rate limiting."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _update_token_usage(self, usage: Dict[str, int]):
        """Update token usage statistics."""
        if usage:
            self.token_usage["total_tokens"] += usage.get("total_tokens", 0)
            self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def _make_completion_request(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make completion request to OpenAI with retry logic.
        
        Args:
            messages (list): Chat messages
            temperature (float): Sampling temperature
            max_tokens (int, optional): Maximum tokens in response
            
        Returns:
            dict: OpenAI response
            
        Raises:
            OpenAIError: If request fails after retries
        """
        await self._rate_limit()
        
        try:
            completion_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens
            
            response = await self.client.chat.completions.create(**completion_kwargs)
            
            # Update token usage
            if hasattr(response, 'usage') and response.usage:
                self._update_token_usage({
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                })
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise OpenAIError(f"Failed to get completion from OpenAI: {str(e)}")
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from OpenAI, with error handling.
        
        Args:
            content (str): Response content
            
        Returns:
            dict: Parsed JSON
            
        Raises:
            OpenAIError: If JSON parsing fails
        """
        try:
            # Try to extract JSON from response if it's embedded in text
            content = content.strip()
            
            # Find JSON block if wrapped in markdown
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            # Clean up common issues
            content = content.replace("'", '"')  # Replace single quotes
            
            parsed = json.loads(content)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {content}")
            
            # Return structured error response
            return {
                "error": "Failed to parse AI response",
                "raw_content": content,
                "summary": "Analysis completed but response format was invalid",
                "questions": [
                    "Can you verify your recent account activity?",
                    "Have you noticed any unauthorized transactions?",
                    "Have you shared your account details with anyone recently?",
                    "Are you aware of any suspicious communications?",
                    "Can you confirm your recent login locations?"
                ],
                "risk_level": "Medium"
            }
    
    async def analyze_fraud_data(
        self, 
        customer_id: str, 
        transaction_data: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze customer data for fraud indicators.
        
        Args:
            customer_id (str): Customer ID
            transaction_data (str): Formatted transaction data
            context (str, optional): Additional context
            
        Returns:
            dict: Analysis results with summary, questions, and risk assessment
        """
        # Skip AI generation and use predefined customer-safe questions
        # This ensures no internal system terms appear in customer-facing questions
        
        try:
            # Analyze data for risk level assessment
            risk_level = "Medium"  # Default
            if "high risk" in transaction_data.lower():
                risk_level = "High"
            elif "fraud_cases_linked_past_30_days: 0" in transaction_data.lower():
                risk_level = "Low"
            
            # Generate summary using AI but use fixed questions
            system_prompt = """
            You are a fraud analyst. Analyze the customer data and provide ONLY a summary of key findings.
            Do NOT generate questions. Focus on describing risk patterns and fraud indicators for analyst review.
            Keep the summary concise and professional. Do NOT mention specific system names.
            Respond with only the summary text, no JSON formatting needed.
            """
            
            user_prompt = f"""
            Analyze this customer data and provide a concise summary of key fraud risk factors:
            
            Customer ID: {customer_id}
            Data: {transaction_data}
            
            Provide only a summary of findings for analyst review.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self._make_completion_request(
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Generate customer-safe questions based on proven patterns
            questions = self._generate_pattern_based_questions()
            
            return {
                "summary": summary,
                "questions": questions,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error(f"Fraud analysis failed: {e}")
            # Return fallback response
            return {
                "summary": f"Analysis completed for customer {customer_id}. Multiple risk factors detected requiring immediate customer verification.",
                "questions": [
                    "Do you believe you are investing with a real firm?",
                    "Was the contact initiated by you or did they contact you first?",
                    "Is there any remote access to your computer or are you currently on a call with them?",
                    "Are there multiple payments set up or any future dated payments?",
                    "Are you hesitant to believe this might be a scam?"
                ],
                "risk_level": "Medium",
                "error": str(e)
            }
    
    async def generate_followup_questions(
        self, 
        customer_id: str,
        analysis_summary: str,
        conversation_context: str = ""
    ) -> List[str]:
        """
        Generate follow-up questions based on analysis and conversation.
        
        Args:
            customer_id (str): Customer ID
            analysis_summary (str): Previous analysis summary
            conversation_context (str): Current conversation context
            
        Returns:
            list: Follow-up questions
        """
        system_prompt = """
        You are helping a banker generate follow-up questions for a fraud investigation.
        Based on the analysis and conversation context, suggest 3-5 specific follow-up questions
        that will help gather more information or clarify suspicious activities.
        
        Return a JSON array of questions.
        """
        
        user_prompt = f"""
        Customer: {customer_id}
        Analysis Summary: {analysis_summary}
        Conversation Context: {conversation_context}
        
        Generate 3-5 relevant follow-up questions as a JSON array.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = await self._make_completion_request(
                messages=messages,
                temperature=0.4,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            questions = self._parse_json_response(content)
            
            if isinstance(questions, list):
                return questions[:5]  # Cap at 5 questions
            else:
                return ["Can you provide more details about the suspicious activity?"]
                
        except Exception as e:
            logger.error(f"Follow-up question generation failed: {e}")
            return ["Can you provide more details about your account activity?"]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            dict: Usage statistics
        """
        return {
            "token_usage": self.token_usage.copy(),
            "model": self.model,
            "api_configured": bool(self.api_key and self.api_key != "your_openai_api_key_here")
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test OpenAI API connection.
        
        Returns:
            dict: Connection test results
        """
        try:
            response = await self._make_completion_request(
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            
            return {
                "status": "success",
                "model": self.model,
                "response_received": bool(response.choices[0].message.content)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model
            }
    
    def _generate_pattern_based_questions(self) -> List[str]:
        """
        Generate customer-safe questions based on proven patterns.
        Creates variations of the 5 core question types for fraud detection.
        
        Returns:
            list: 5 customer-safe questions following proven patterns
        """
        import random
        
        # Pattern 1: Investment legitimacy questions
        investment_questions = [
            "Do you believe you are investing with a real firm?",
            "Are you confident this investment opportunity is legitimate?",
            "Do you trust that the company you're investing with is genuine?",
            "Have you verified that this investment firm is real and regulated?",
            "Are you certain the investment platform you're using is authentic?"
        ]
        
        # Pattern 2: Contact initiation questions
        contact_questions = [
            "Was the contact initiated by you or did they contact you first?",
            "Did you reach out to them, or did they approach you initially?",
            "Who made the first contact - you or the investment company?",
            "Did you find them through your own research, or did they contact you directly?",
            "Were you the one who started this conversation, or did they call you first?"
        ]
        
        # Pattern 3: Remote access questions
        access_questions = [
            "Is there any remote access to your computer or are you currently on a call with them?",
            "Do they have access to your computer remotely, or are you speaking with them right now?",
            "Are you currently connected to them through your computer or on a phone call?",
            "Have you given them remote control of your device, or are you talking to them now?",
            "Is someone accessing your computer from their end, or are you in contact with them at the moment?"
        ]
        
        # Pattern 4: Payment pattern questions
        payment_questions = [
            "Are there multiple payments set up or any future dated payments?",
            "Have you scheduled several payments or any upcoming automatic transfers?",
            "Are there multiple transactions arranged or any payments planned for later?",
            "Have you set up recurring payments or any future-dated transfers?",
            "Are there several payment installments or any scheduled transactions coming up?"
        ]
        
        # Pattern 5: Scam resistance questions
        resistance_questions = [
            "Are you hesitant to believe this might be a scam?",
            "Do you have any doubts that this could potentially be fraudulent?",
            "Are you concerned this might not be legitimate?",
            "Do you suspect this could be a scam or fraud attempt?",
            "Are you questioning whether this investment opportunity is genuine?"
        ]
        
        # Select one random question from each pattern
        selected_questions = [
            random.choice(investment_questions),
            random.choice(contact_questions), 
            random.choice(access_questions),
            random.choice(payment_questions),
            random.choice(resistance_questions)
        ]
        
        return selected_questions

# Global service instance
ai_service = OpenAIService()