"""Utility functions"""


def generate_username_from_email(email: str) -> str:
    """Generate a username from email address"""
    # Extract part before @ and clean it
    username = email.split('@')[0]
    # Remove special characters and keep alphanumeric + underscore
    username = ''.join(c if c.isalnum() or c == '_' else '_' for c in username)
    return username.lower()
