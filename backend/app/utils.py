"""
Utility functions for the tax consultant application
"""
import re


def contains_sensitive_info(message: str) -> bool:
    """
    Check if message contains sensitive personal information
    Extracted from tax_consultant.py for reuse
    """
    sensitive_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',    # SSN format (123-45-6789)
        r'\b\d{9}\b',                # 9-digit numbers (potential SIN/SSN)
        r'\b\d{3}\s\d{3}\s\d{3}\b',  # SIN format with spaces (123 456 789)
        r'\b\d{3}-\d{3}-\d{3}\b',    # SIN format with dashes (123-456-789)
        r'\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b',  # Credit card format
        r'\b[A-Z]\d{8}[A-Z]?\b',     # Passport format (rough)
    ]

    for pattern in sensitive_patterns:
        if re.search(pattern, message):
            return True
    return False


def sanitize_message(message: str) -> str:
    """
    Sanitize message by replacing sensitive patterns with placeholders
    """
    # Replace SSN patterns
    message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN-REDACTED]', message)
    message = re.sub(r'\b\d{9}\b', '[ID-REDACTED]', message)
    message = re.sub(r'\b\d{3}\s\d{3}\s\d{3}\b', '[SIN-REDACTED]', message)
    message = re.sub(r'\b\d{3}-\d{3}-\d{3}\b', '[SIN-REDACTED]', message)

    return message


def get_sensitive_info_error_message() -> str:
    """
    Get the standard error message for sensitive information
    """
    return ("Please don't share sensitive personal identifiers like SSN, SIN, passport numbers, "
            "or full account numbers. I can help with general tax situations without this information.")