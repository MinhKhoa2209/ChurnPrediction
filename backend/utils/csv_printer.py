"""
CSV Pretty Printer Service
It ensures proper formatting, numeric precision, and RFC 4180 compliance.
"""

import csv
import io
from typing import Any, Dict, List, Optional, Union


class CSVPrettyPrinter:
    """
    CSV Pretty Printer for formatting customer records and predictions.
    
    This class handles:
    - Formatting customer records with predictions into CSV format
    - Including all original columns plus Churn_Probability column
    - Formatting numeric values with 2 decimal places
    - Escaping special characters according to RFC 4180
    
    - 14.2: Include all original columns plus Churn_Probability column
    - 14.3: Format numeric values with 2 decimal places
    - 14.4: Escape special characters according to RFC 4180
    """
    
    # Standard column order for customer records (matches dataset schema)
    STANDARD_COLUMNS = [
        "customerID",
        "gender",
        "SeniorCitizen",
        "Partner",
        "Dependents",
        "tenure",
        "PhoneService",
        "MultipleLines",
        "InternetService",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
        "Contract",
        "PaperlessBilling",
        "PaymentMethod",
        "MonthlyCharges",
        "TotalCharges",
        "Churn"
    ]
    
    # Numeric columns that should be formatted with 2 decimal places
    NUMERIC_COLUMNS = {
        "MonthlyCharges",
        "TotalCharges",
        "Churn_Probability"
    }
    
    def __init__(self):
        """Initialize CSV Pretty Printer"""
        pass
    
    def format(
        self,
        records: List[Dict[str, Any]],
        include_probability: bool = False
    ) -> str:
        """
        Format customer records into CSV string.
        
        This method converts a list of customer records (optionally with predictions)
        into a properly formatted CSV string following RFC 4180 standards.
        
        - 14.2: Include all original columns plus Churn_Probability column
        - 14.3: Format numeric values with 2 decimal places
        - 14.4: Escape special characters according to RFC 4180
        
        Args:
            records: List of dictionaries containing customer data
            include_probability: Whether to include Churn_Probability column
            
        Returns:
            CSV-formatted string with proper escaping and formatting
            
        Example:
            >>> printer = CSVPrettyPrinter()
            >>> records = [
            ...     {
            ...         "customerID": "TEST-001",
            ...         "gender": "Male",
            ...         "tenure": 12,
            ...         "MonthlyCharges": 50.5,
            ...         "TotalCharges": 606.0,
            ...         "Churn": "No",
            ...         "Churn_Probability": 0.234
            ...     }
            ... ]
            >>> csv_string = printer.format(records, include_probability=True)
        """
        if not records:
            return ""
        
        # Determine columns to include
        columns = self._determine_columns(records, include_probability)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            quoting=csv.QUOTE_MINIMAL,  # RFC 4180: quote only when necessary
            lineterminator='\n'  # RFC 4180: use LF or CRLF
        )
        
        # Write header
        writer.writeheader()
        
        # Write data rows with proper formatting
        for record in records:
            formatted_record = self._format_record(record, columns)
            writer.writerow(formatted_record)
        
        # Get CSV string
        csv_string = output.getvalue()
        output.close()
        
        return csv_string
    
    def format_predictions(
        self,
        predictions: List[Dict[str, Any]]
    ) -> str:
        """
        Format prediction results into CSV string.
        
        This is a convenience method specifically for formatting predictions
        with customer data and churn probabilities.
        
        - 14.2: Include all original columns plus Churn_Probability column
        
        Args:
            predictions: List of prediction dictionaries containing:
                - input_features: Original customer data
                - probability: Churn probability (0.0 to 1.0)
                
        Returns:
            CSV-formatted string with customer data and Churn_Probability
            
        Example:
            >>> printer = CSVPrettyPrinter()
            >>> predictions = [
            ...     {
            ...         "input_features": {
            ...             "customerID": "TEST-001",
            ...             "gender": "Male",
            ...             "tenure": 12,
            ...             "MonthlyCharges": 50.5,
            ...             "TotalCharges": 606.0,
            ...             "Churn": "No"
            ...         },
            ...         "probability": 0.234
            ...     }
            ... ]
            >>> csv_string = printer.format_predictions(predictions)
        """
        # Transform predictions into flat records
        records = []
        for pred in predictions:
            # Extract input features
            record = dict(pred.get("input_features", {}))
            
            # Add churn probability
            probability = pred.get("probability", 0.0)
            record["Churn_Probability"] = probability
            
            records.append(record)
        
        return self.format(records, include_probability=True)
    
    def _determine_columns(
        self,
        records: List[Dict[str, Any]],
        include_probability: bool
    ) -> List[str]:
        """
        Determine the column order for CSV output.
        
        Uses standard column order when possible, falling back to
        alphabetical order for any additional columns.
        
        Args:
            records: List of record dictionaries
            include_probability: Whether to include Churn_Probability column
            
        Returns:
            Ordered list of column names
        """
        if not records:
            return []
        
        # Get all unique keys from all records
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        
        # Start with standard columns that exist in the data
        columns = [col for col in self.STANDARD_COLUMNS if col in all_keys]
        
        # Add Churn_Probability if requested and present
        if include_probability and "Churn_Probability" in all_keys:
            columns.append("Churn_Probability")
        
        # Add any additional columns not in standard list (sorted alphabetically)
        additional_columns = sorted(
            all_keys - set(columns) - {"Churn_Probability"}
        )
        columns.extend(additional_columns)
        
        return columns
    
    def _format_record(
        self,
        record: Dict[str, Any],
        columns: List[str]
    ) -> Dict[str, str]:
        """
        Format a single record for CSV output.
        
        This method handles:
        - Numeric formatting (2 decimal places)
        - Type conversion to strings
        - Handling missing values
        
        Requirement 14.3: Format numeric values with 2 decimal places
        
        Args:
            record: Dictionary containing record data
            columns: Ordered list of columns to include
            
        Returns:
            Dictionary with formatted string values
        """
        formatted = {}
        
        for column in columns:
            value = record.get(column)
            formatted[column] = self._format_value(column, value)
        
        return formatted
    
    def _format_value(self, column: str, value: Any) -> str:
        """
        Format a single value for CSV output.
        
        Handles:
        - Numeric values: format with 2 decimal places
        - None/empty values: return empty string
        - Other values: convert to string
        
        Requirement 14.3: Format numeric values with 2 decimal places
        
        Args:
            column: Column name (used to determine formatting)
            value: Value to format
            
        Returns:
            Formatted string value
        """
        # Handle None and empty values
        if value is None:
            return ""
        
        # Handle numeric columns with 2 decimal places
        if column in self.NUMERIC_COLUMNS:
            try:
                # Convert to float and format with 2 decimal places
                numeric_value = float(value)
                return f"{numeric_value:.2f}"
            except (ValueError, TypeError):
                # If conversion fails, return as string
                return str(value)
        
        # Handle boolean values (convert to Yes/No for Churn column)
        if column == "Churn" and isinstance(value, bool):
            return "Yes" if value else "No"
        
        # Handle SeniorCitizen (should be 0 or 1)
        if column == "SeniorCitizen" and isinstance(value, (int, bool)):
            return str(int(value))
        
        # Handle tenure (should be integer)
        if column == "tenure" and isinstance(value, (int, float)):
            return str(int(value))
        
        # Default: convert to string
        return str(value)
    
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate that a record contains required fields.
        
        Args:
            record: Dictionary containing record data
            
        Returns:
            True if record is valid, False otherwise
        """
        # At minimum, a record should have customerID
        return "customerID" in record and bool(record["customerID"])
    
    def get_standard_columns(self) -> List[str]:
        """
        Get the standard column order for customer records.
        
        Returns:
            List of standard column names in order
        """
        return self.STANDARD_COLUMNS.copy()
    
    def get_numeric_columns(self) -> List[str]:
        """
        Get the list of numeric columns that require special formatting.
        
        Returns:
            List of numeric column names
        """
        return list(self.NUMERIC_COLUMNS)


# Convenience function for quick formatting
def format_customer_records(
    records: List[Dict[str, Any]],
    include_probability: bool = False
) -> str:
    """
    Convenience function to format customer records into CSV.
    
    Args:
        records: List of customer record dictionaries
        include_probability: Whether to include Churn_Probability column
        
    Returns:
        CSV-formatted string
    """
    printer = CSVPrettyPrinter()
    return printer.format(records, include_probability=include_probability)


def format_predictions(predictions: List[Dict[str, Any]]) -> str:
    """
    Convenience function to format predictions into CSV.
    
    Args:
        predictions: List of prediction dictionaries
        
    Returns:
        CSV-formatted string with Churn_Probability column
    """
    printer = CSVPrettyPrinter()
    return printer.format_predictions(predictions)
