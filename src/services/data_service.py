"""
Data Service for Excel Processing

This module handles loading and processing customer transaction data
from Excel files using pandas for fraud analysis.
"""

import os
import pandas as pd
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class CustomerDataService:
    """Service for managing customer transaction data."""
    
    def __init__(self, data_file_path: Optional[str] = None):
        """
        Initialize the data service.
        
        Args:
            data_file_path (str, optional): Path to Excel data file
        """
        self.data_file_path = data_file_path or os.getenv("DATA_FILE_PATH", "data/fraud_data.xlsx")
        self._data_cache: Optional[pd.DataFrame] = None
    
    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Load data from Excel file with caching.
        
        Args:
            force_reload (bool): Force reload of data ignoring cache
            
        Returns:
            pd.DataFrame: Customer transaction data
            
        Raises:
            FileNotFoundError: If data file doesn't exist
            Exception: For other data loading errors
        """
        if self._data_cache is None or force_reload:
            if not os.path.exists(self.data_file_path):
                raise FileNotFoundError(f"Data file not found: {self.data_file_path}")
            
            try:
                # Read Excel file with proper encoding handling
                self._data_cache = pd.read_excel(
                    self.data_file_path,
                    engine='openpyxl'
                )
                # Ensure consistent column naming
                self._data_cache.columns = self._data_cache.columns.str.strip()
                
            except Exception as e:
                raise Exception(f"Error loading data from {self.data_file_path}: {str(e)}")
        
        return self._data_cache
    
    def get_customer_data(self, customer_id: str) -> pd.DataFrame:
        """
        Retrieve data for a specific customer.
        
        Args:
            customer_id (str): Customer ID to search for
            
        Returns:
            pd.DataFrame: Customer-specific transaction data
            
        Raises:
            ValueError: If customer_id is invalid
            FileNotFoundError: If customer not found
        """
        if not customer_id or not customer_id.strip():
            raise ValueError("Customer ID is required")
        
        customer_id = customer_id.strip()
        data = self.load_data()
        
        # Find customer data using the correct column name
        customer_column = 'Customer_CGID'  # Based on actual data structure
        if customer_column not in data.columns:
            # Fallback to other possible column names
            possible_columns = ['customer_id', 'Customer_ID', 'CUSTOMER_ID', 'CustomerID']
            customer_column = None
            for col in possible_columns:
                if col in data.columns:
                    customer_column = col
                    break
            
            if not customer_column:
                raise Exception(f"No customer ID column found. Available columns: {list(data.columns)}")
        
        # Filter data for specific customer
        customer_data = data[data[customer_column].astype(str) == str(customer_id)]
        
        if customer_data.empty:
            raise FileNotFoundError(f"Customer {customer_id} not found in data")
        
        return customer_data
    
    def get_customer_summary(self, customer_id: str) -> Dict[str, Any]:
        """
        Get summarized customer information for analysis.
        
        Args:
            customer_id (str): Customer ID
            
        Returns:
            dict: Summarized customer data
        """
        customer_data = self.get_customer_data(customer_id)
        
        if customer_data.empty:
            return {}
        
        # Extract first row for summary (assuming one row per customer)
        row = customer_data.iloc[0]
        
        summary = {
            "customer_id": customer_id,
            "account_details": {
                "bsb": row.get('BSB', 'N/A'),
                "account": row.get('ACCOUNT', 'N/A')
            },
            "risk_flags": {
                "biocatch_flag": row.get('BIOCATCH_FLAG', 'N/A'),
                "group_ib_flag": row.get('GROUP_IB_FLAG', 'N/A'), 
                "sasfm_flag": row.get('SASFM_FLAG', 'N/A'),
                "isod_flag": row.get('ISOD_FLAG', 'N/A')
            },
            "fraud_history": {
                "cases_past_30_days": row.get('Fraud_Cases_Linked_Past_30_Days', 0)
            },
            "raw_data": customer_data.to_dict('records')
        }
        
        return summary
    
    def format_for_ai_analysis(self, customer_data: pd.DataFrame) -> str:
        """
        Format customer data for OpenAI analysis.
        Remove internal system names to prevent them appearing in customer questions.
        
        Args:
            customer_data (pd.DataFrame): Customer transaction data
            
        Returns:
            str: Formatted text for AI analysis (sanitized for customer-facing questions)
        """
        if customer_data.empty:
            return "No customer data available"
        
        # Get first row for analysis
        row = customer_data.iloc[0]
        
        # Map risk levels without exposing system names
        risk_flags = []
        for flag_col in ['BIOCATCH_FLAG', 'GROUP_IB_FLAG', 'SASFM_FLAG', 'ISOD_FLAG']:
            if flag_col in row:
                flag_value = row.get(flag_col, 'N/A')
                if 'high risk' in str(flag_value).lower():
                    risk_flags.append('High Risk Indicator')
                elif 'medium risk' in str(flag_value).lower():
                    risk_flags.append('Medium Risk Indicator')
                elif 'low risk' in str(flag_value).lower():
                    risk_flags.append('Low Risk Indicator')
        
        fraud_cases = row.get('Fraud_Cases_Linked_Past_30_Days', 0)
        
        formatted_text = f"""
        Customer Analysis Report:
        
        Customer ID: {row.get('Customer_CGID', 'N/A')}
        Account Details: BSB {row.get('BSB', 'N/A')}, Account {row.get('ACCOUNT', 'N/A')}
        
        Risk Assessment Summary:
        - Total Risk Indicators Detected: {len(risk_flags)}
        - Risk Levels Found: {', '.join(risk_flags) if risk_flags else 'None'}
        
        Fraud History:
        - Previous Fraud Cases: {fraud_cases} in past 30 days
        
        Analysis Notes:
        Customer has {'multiple risk indicators' if len(risk_flags) > 2 else 'some risk indicators' if risk_flags else 'minimal risk indicators'} detected through automated screening systems.
        {'Previous fraud activity detected.' if fraud_cases > 0 else 'No previous fraud cases on record.'}
        
        IMPORTANT: Generate customer-friendly questions only. Do NOT mention system names or technical terms.
        """
        
        return formatted_text.strip()
    
    def get_available_customers(self) -> List[str]:
        """
        Get list of available customer IDs.
        
        Returns:
            list: List of customer IDs
        """
        data = self.load_data()
        customer_column = 'Customer_CGID'  # Based on actual data structure
        
        if customer_column in data.columns:
            return data[customer_column].astype(str).unique().tolist()
        
        return []
    
    def get_data_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded data.
        
        Returns:
            dict: Data information including shape, columns, etc.
        """
        data = self.load_data()
        
        return {
            "file_path": self.data_file_path,
            "shape": data.shape,
            "columns": list(data.columns),
            "total_customers": len(self.get_available_customers()),
            "data_types": data.dtypes.to_dict()
        }

# Global instance for use across the application
customer_data_service = CustomerDataService()