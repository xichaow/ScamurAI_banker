"""
Excel Utilities

Helper functions for Excel data processing, validation, and manipulation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# Setup logging
logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Utility class for Excel data processing operations."""
    
    @staticmethod
    def validate_excel_file(file_path: str) -> bool:
        """
        Validate if Excel file exists and is readable.
        
        Args:
            file_path (str): Path to Excel file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Excel file not found: {file_path}")
                return False
            
            if not path.suffix.lower() in ['.xlsx', '.xls']:
                logger.error(f"Invalid file format: {file_path}")
                return False
            
            # Try to read first few rows to validate
            pd.read_excel(file_path, nrows=1)
            return True
            
        except Exception as e:
            logger.error(f"Excel file validation failed: {e}")
            return False
    
    @staticmethod
    def get_excel_info(file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about Excel file.
        
        Args:
            file_path (str): Path to Excel file
            
        Returns:
            dict: File information including sheets, columns, shape, etc.
        """
        try:
            # Get basic file info
            path = Path(file_path)
            file_info = {
                "file_path": str(path.absolute()),
                "file_size_mb": path.stat().st_size / (1024 * 1024),
                "file_extension": path.suffix
            }
            
            # Load Excel file
            with pd.ExcelFile(file_path) as xl:
                file_info["sheet_names"] = xl.sheet_names
                
                # Get info for each sheet
                sheet_info = {}
                for sheet in xl.sheet_names:
                    df = xl.parse(sheet, nrows=0)  # Just headers
                    sheet_info[sheet] = {
                        "columns": list(df.columns),
                        "column_count": len(df.columns)
                    }
                    
                    # Get full shape for first sheet
                    if sheet == xl.sheet_names[0]:
                        df_full = xl.parse(sheet)
                        sheet_info[sheet]["shape"] = df_full.shape
                        sheet_info[sheet]["data_types"] = df_full.dtypes.to_dict()
                
                file_info["sheets"] = sheet_info
            
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to get Excel info: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names for consistency.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with standardized column names
        """
        df_copy = df.copy()
        
        # Strip whitespace and standardize naming
        df_copy.columns = df_copy.columns.str.strip()
        df_copy.columns = df_copy.columns.str.replace(' ', '_')
        df_copy.columns = df_copy.columns.str.replace('-', '_')
        
        # Common column name mappings
        column_mappings = {
            'customer_cgid': 'Customer_CGID',
            'customerid': 'Customer_CGID',
            'customer_id': 'Customer_CGID',
            'custid': 'Customer_CGID',
        }
        
        # Apply mappings (case insensitive)
        for old_col in df_copy.columns:
            lower_col = old_col.lower()
            if lower_col in column_mappings:
                df_copy.rename(columns={old_col: column_mappings[lower_col]}, inplace=True)
        
        return df_copy
    
    @staticmethod
    def detect_fraud_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect potential fraud indicators in the dataset.
        
        Args:
            df (pd.DataFrame): Customer data
            
        Returns:
            dict: Fraud indicators and statistics
        """
        indicators = {
            "high_risk_customers": 0,
            "customers_with_fraud_history": 0,
            "multiple_risk_flags": 0,
            "risk_flag_distribution": {},
            "fraud_case_statistics": {}
        }
        
        try:
            # Count high risk customers
            risk_columns = ['BIOCATCH_FLAG', 'GROUP_IB_FLAG', 'SASFM_FLAG', 'ISOD_FLAG']
            
            for col in risk_columns:
                if col in df.columns:
                    risk_dist = df[col].value_counts().to_dict()
                    indicators["risk_flag_distribution"][col] = risk_dist
                    
                    # Count high risk
                    high_risk_count = df[df[col].str.contains('high', case=False, na=False)].shape[0]
                    indicators["high_risk_customers"] += high_risk_count
            
            # Fraud history analysis
            fraud_col = 'Fraud_Cases_Linked_Past_30_Days'
            if fraud_col in df.columns:
                fraud_stats = {
                    "total_cases": df[fraud_col].sum(),
                    "customers_with_cases": (df[fraud_col] > 0).sum(),
                    "max_cases_per_customer": df[fraud_col].max(),
                    "avg_cases": df[fraud_col].mean()
                }
                indicators["fraud_case_statistics"] = fraud_stats
                indicators["customers_with_fraud_history"] = fraud_stats["customers_with_cases"]
            
            # Multiple risk flags
            risk_flag_count = 0
            for _, row in df.iterrows():
                high_risk_flags = 0
                for col in risk_columns:
                    if col in df.columns and 'high' in str(row[col]).lower():
                        high_risk_flags += 1
                
                if high_risk_flags >= 2:
                    risk_flag_count += 1
            
            indicators["multiple_risk_flags"] = risk_flag_count
            
        except Exception as e:
            logger.error(f"Error detecting fraud indicators: {e}")
            indicators["error"] = str(e)
        
        return indicators

class DataValidator:
    """Data validation utilities."""
    
    @staticmethod
    def validate_customer_data(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate customer data integrity.
        
        Args:
            df (pd.DataFrame): Customer data to validate
            
        Returns:
            dict: Validation results
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        # Required columns check
        required_columns = ['Customer_CGID']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation["errors"].append(f"Missing required columns: {missing_columns}")
            validation["is_valid"] = False
        
        # Data quality checks
        if 'Customer_CGID' in df.columns:
            # Check for null customer IDs
            null_customers = df['Customer_CGID'].isnull().sum()
            if null_customers > 0:
                validation["warnings"].append(f"{null_customers} rows with null Customer_CGID")
            
            # Check for duplicate customer IDs
            duplicates = df['Customer_CGID'].duplicated().sum()
            if duplicates > 0:
                validation["warnings"].append(f"{duplicates} duplicate Customer_CGID entries")
        
        # Statistical validation
        validation["statistics"] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "null_values_per_column": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.to_dict()
        }
        
        return validation
    
    @staticmethod
    def validate_risk_flags(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate risk flag data.
        
        Args:
            df (pd.DataFrame): Data with risk flags
            
        Returns:
            dict: Risk flag validation results
        """
        validation = {
            "valid_risk_levels": ["low risk", "medium risk", "high risk", "N/A"],
            "invalid_entries": {},
            "is_valid": True
        }
        
        risk_columns = ['BIOCATCH_FLAG', 'GROUP_IB_FLAG', 'SASFM_FLAG', 'ISOD_FLAG']
        
        for col in risk_columns:
            if col in df.columns:
                unique_values = df[col].unique()
                invalid_values = [val for val in unique_values 
                                if str(val).lower() not in [v.lower() for v in validation["valid_risk_levels"]]]
                
                if invalid_values:
                    validation["invalid_entries"][col] = invalid_values
                    validation["is_valid"] = False
        
        return validation

class DataExporter:
    """Data export utilities."""
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, file_path: str, sheet_name: str = "Data") -> bool:
        """
        Export DataFrame to Excel file.
        
        Args:
            df (pd.DataFrame): Data to export
            file_path (str): Output file path
            sheet_name (str): Name of Excel sheet
            
        Returns:
            bool: True if export successful
        """
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"Data exported successfully to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    @staticmethod
    def export_analysis_summary(analysis_data: Dict[str, Any], file_path: str) -> bool:
        """
        Export analysis summary to Excel with multiple sheets.
        
        Args:
            analysis_data (dict): Analysis results
            file_path (str): Output file path
            
        Returns:
            bool: True if export successful
        """
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame.from_dict(
                    analysis_data.get('summary', {}), 
                    orient='index',
                    columns=['Value']
                )
                summary_df.to_excel(writer, sheet_name='Summary')
                
                # Risk distribution sheet
                if 'risk_distribution' in analysis_data:
                    risk_df = pd.DataFrame(analysis_data['risk_distribution'])
                    risk_df.to_excel(writer, sheet_name='Risk_Distribution', index=False)
                
                # Customer details sheet
                if 'customer_details' in analysis_data:
                    details_df = pd.DataFrame(analysis_data['customer_details'])
                    details_df.to_excel(writer, sheet_name='Customer_Details', index=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Analysis export failed: {e}")
            return False

# Convenience functions
def quick_excel_info(file_path: str) -> Dict[str, Any]:
    """Quick Excel file information."""
    return ExcelProcessor.get_excel_info(file_path)

def validate_fraud_data(file_path: str) -> Dict[str, Any]:
    """Validate fraud data file."""
    try:
        df = pd.read_excel(file_path)
        df = ExcelProcessor.standardize_column_names(df)
        
        validation = DataValidator.validate_customer_data(df)
        risk_validation = DataValidator.validate_risk_flags(df)
        fraud_indicators = ExcelProcessor.detect_fraud_indicators(df)
        
        return {
            "data_validation": validation,
            "risk_validation": risk_validation, 
            "fraud_indicators": fraud_indicators
        }
        
    except Exception as e:
        return {"error": str(e)}

def process_customer_file(file_path: str) -> pd.DataFrame:
    """Process customer file with standardization."""
    df = pd.read_excel(file_path)
    df = ExcelProcessor.standardize_column_names(df)
    return df