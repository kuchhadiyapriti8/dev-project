from flask_hashing import Hashing

def generate_hashed_password(password, salt):
    """Generate a hashed password using the provided salt."""
    return hashing.hash_value(password, salt=salt)

def verify_password(stored_password_hash, provided_password, salt):
    """Verify a provided password against the stored hash."""
    return hashing.check_value(stored_password_hash, provided_password,salt)
