import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert password to bytes
    pwd_bytes = password.encode('utf-8')
    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    # Return as a string for database storage
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        # Convert both to bytes for comparison
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # Check if they match
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False
