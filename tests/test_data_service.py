"""
Unit tests for data service functionality.

Tests Excel data loading, customer data retrieval, and data formatting.
"""

import pytest
import pandas as pd
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.data_service import CustomerDataService

class TestCustomerDataService:
    """Test cases for CustomerDataService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create test data
        self.test_data = pd.DataFrame({
            'Customer_CGID': ['12345', '67890', '11111'],
            'BSB': ['803-323', '808-202', '809-111'],
            'ACCOUNT': ['123456789', '987654321', '555666777'],
            'BIOCATCH_FLAG': ['high risk', 'low risk', 'medium risk'],
            'GROUP_IB_FLAG': ['high risk', 'medium risk', 'low risk'],
            'SASFM_FLAG': ['medium risk', 'low risk', 'high risk'],
            'ISOD_FLAG': ['low risk', 'medium risk', 'high risk'],
            'Fraud_Cases_Linked_Past_30_Days': [1, 0, 3]
        })
        
        # Create service with test data file path
        self.service = CustomerDataService('test_data.xlsx')
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_load_data_success(self, mock_exists, mock_read_excel):
        """Test successful data loading."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result = self.service.load_data()
        
        # Assert
        assert not result.empty
        assert len(result) == 3
        assert 'Customer_CGID' in result.columns
        mock_read_excel.assert_called_once()
    
    @patch('os.path.exists')
    def test_load_data_file_not_found(self, mock_exists):
        """Test data loading with missing file."""
        # Arrange
        mock_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.service.load_data()
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_load_data_with_caching(self, mock_exists, mock_read_excel):
        """Test data loading uses caching properly."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result1 = self.service.load_data()
        result2 = self.service.load_data()
        
        # Assert
        mock_read_excel.assert_called_once()  # Should only be called once due to caching
        assert result1.equals(result2)
    
    @patch('pandas.read_excel')
    @patch('os.path.exists') 
    def test_get_customer_data_success(self, mock_exists, mock_read_excel):
        """Test successful customer data retrieval."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result = self.service.get_customer_data('12345')
        
        # Assert
        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]['Customer_CGID'] == '12345'
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_get_customer_data_not_found(self, mock_exists, mock_read_excel):
        """Test customer data retrieval with invalid customer ID."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            self.service.get_customer_data('99999')
    
    def test_get_customer_data_invalid_id(self):
        """Test customer data retrieval with invalid input."""
        # Test empty string
        with pytest.raises(ValueError):
            self.service.get_customer_data('')
        
        # Test None
        with pytest.raises(ValueError):
            self.service.get_customer_data(None)
        
        # Test whitespace only
        with pytest.raises(ValueError):
            self.service.get_customer_data('   ')
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_get_customer_summary(self, mock_exists, mock_read_excel):
        """Test customer summary generation."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result = self.service.get_customer_summary('12345')
        
        # Assert
        assert result['customer_id'] == '12345'
        assert 'account_details' in result
        assert 'risk_flags' in result
        assert 'fraud_history' in result
        assert result['account_details']['bsb'] == '803-323'
        assert result['fraud_history']['cases_past_30_days'] == 1
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_format_for_ai_analysis(self, mock_exists, mock_read_excel):
        """Test AI formatting functionality."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        customer_data = self.test_data[self.test_data['Customer_CGID'] == '12345']
        
        # Act
        result = self.service.format_for_ai_analysis(customer_data)
        
        # Assert
        assert isinstance(result, str)
        assert '12345' in result
        assert 'high risk' in result
        assert 'Customer Analysis Report' in result
    
    def test_format_for_ai_analysis_empty_data(self):
        """Test AI formatting with empty data."""
        # Arrange
        empty_data = pd.DataFrame()
        
        # Act
        result = self.service.format_for_ai_analysis(empty_data)
        
        # Assert
        assert result == "No customer data available"
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_get_available_customers(self, mock_exists, mock_read_excel):
        """Test getting list of available customers."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result = self.service.get_available_customers()
        
        # Assert
        assert isinstance(result, list)
        assert '12345' in result
        assert '67890' in result
        assert '11111' in result
        assert len(result) == 3
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_get_data_info(self, mock_exists, mock_read_excel):
        """Test data information retrieval."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result = self.service.get_data_info()
        
        # Assert
        assert 'file_path' in result
        assert 'shape' in result
        assert 'columns' in result
        assert 'total_customers' in result
        assert result['shape'] == (3, 8)
        assert result['total_customers'] == 3
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_column_name_flexibility(self, mock_exists, mock_read_excel):
        """Test handling of different customer ID column names."""
        # Arrange - data with different column name
        alt_data = self.test_data.rename(columns={'Customer_CGID': 'customer_id'})
        mock_exists.return_value = True
        mock_read_excel.return_value = alt_data
        
        # Act
        result = self.service.get_customer_data('12345')
        
        # Assert
        assert not result.empty
        assert len(result) == 1
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_force_reload_data(self, mock_exists, mock_read_excel):
        """Test forcing data reload bypasses cache."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.return_value = self.test_data
        
        # Act
        result1 = self.service.load_data()  # First load
        result2 = self.service.load_data(force_reload=True)  # Force reload
        
        # Assert
        assert mock_read_excel.call_count == 2  # Should be called twice
        assert result1.equals(result2)

# Test edge cases and error conditions
class TestDataServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_file_path(self):
        """Test initialization with invalid file path."""
        service = CustomerDataService('/non/existent/path.xlsx')
        
        with pytest.raises(FileNotFoundError):
            service.load_data()
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_corrupted_excel_file(self, mock_exists, mock_read_excel):
        """Test handling of corrupted Excel file."""
        # Arrange
        mock_exists.return_value = True
        mock_read_excel.side_effect = Exception("Corrupted file")
        service = CustomerDataService('corrupted.xlsx')
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            service.load_data()
        
        assert "Error loading data" in str(exc_info.value)
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_missing_customer_column(self, mock_exists, mock_read_excel):
        """Test handling data without customer ID column."""
        # Arrange
        bad_data = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        mock_exists.return_value = True
        mock_read_excel.return_value = bad_data
        service = CustomerDataService('bad_data.xlsx')
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            service.get_customer_data('12345')
        
        assert "No customer ID column found" in str(exc_info.value)

if __name__ == '__main__':
    pytest.main([__file__])